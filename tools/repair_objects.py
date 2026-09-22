"""Restore objects missing from the local tiec odb (time-budgeted, retrying).

Sources per object, in order:
  1. lazy fetch through a blobless partial clone of GitHub tiec (reachable objects)
  2. GitHub REST API git/blobs via the gh CLI (also serves orphaned objects)
Each restored blob is content-verified: `git hash-object -w` must return the SHA.

usage: repair_objects.py <seconds-budget> [missing-blobs-list]
env:   GH_TOKEN    (only used to sanity-check; gh carries its own auth)
       TIEC_ROOT   repo root                     (default: cwd)
       TIEC_PARTIAL blobless partial clone dir   (default: <root>/../_tiec_verify/tiec_partial)
       TIEC_GITBIN PortableGit bin dir           (default: whatever git is on PATH)
       TIEC_REPAIR_LOG repair log                (default: <root>/../_tiec_verify/repair.log)
       TIEC_REPOS  comma-separated owner/repo list to pull objects from
                   (default: tie-lang/tiec,tie-lang/tiec_v3)
"""
import base64
import json
import os
import subprocess
import sys
import time

ROOT = os.environ.get("TIEC_ROOT") or os.getcwd()
_VERIFY = os.path.abspath(os.path.join(ROOT, os.pardir, "_tiec_verify"))
GITBIN = os.environ.get("TIEC_GITBIN") or ""
GH = os.environ.get("TIEC_GH") or "gh"
SRC = os.environ.get("TIEC_PARTIAL") or os.path.join(_VERIFY, "tiec_partial")
DST = ROOT
LIST = sys.argv[2] if len(sys.argv) > 2 else os.path.join(_VERIFY, "missing_blobs.txt")
LOG = os.environ.get("TIEC_REPAIR_LOG") or os.path.join(_VERIFY, "repair.log")
REPOS = tuple(
    r for r in (os.environ.get("TIEC_REPOS") or "tie-lang/tiec,tie-lang/tiec_v3").split(",") if r
)

env = os.environ.copy()
if GITBIN:
    env["PATH"] = GITBIN + os.pathsep + env.get("PATH", "")


def run(cmd, cwd=None, timeout=60, input=None):
    try:
        return subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout,
                              input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.TimeoutExpired:
        return None


def git(args, cwd, timeout=60, input=None):
    return run(["git"] + args, cwd=cwd, timeout=timeout, input=input)


def present(sha):
    r = git(["cat-file", "-e", sha], DST, timeout=20)
    return r is not None and r.returncode == 0


def from_lazy(sha):
    r = git(["cat-file", "blob", sha], SRC, timeout=15)
    if r is not None and r.returncode == 0:
        return r.stdout
    return None


def from_api(sha):
    for repo in REPOS:
        r = run([GH, "api", "/repos/%s/git/blobs/%s" % (repo, sha)], timeout=25)
        if r is None or r.returncode != 0:
            continue
        try:
            payload = json.loads(r.stdout.decode("utf-8"))
        except ValueError:
            continue
        if payload.get("encoding") == "base64":
            return base64.b64decode(payload["content"])
        return payload["content"].encode("utf-8")
    return None


def log(line):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 80.0
    t0 = time.time()
    with open(LIST, encoding="utf-8") as f:
        shas = [l.strip() for l in f if l.strip()]
    todo = [s for s in shas if not present(s)]
    log("=== round start: %d missing, budget %.0fs ===" % (len(todo), budget))
    ok = bad = 0
    for sha in todo:
        if time.time() - t0 > budget:
            break
        data, how = None, ""
        for attempt in range(2):
            data = from_lazy(sha)
            if data:
                how = "lazy"
                break
            data = from_api(sha)
            if data:
                how = "api"
                break
            time.sleep(2)
        if not data:
            bad += 1
            log("FAIL  %s (unavailable this round)" % sha)
            time.sleep(1)
            continue
        w = git(["hash-object", "-w", "--stdin"], DST, timeout=60, input=data)
        got = w.stdout.decode().strip() if w else ""
        if got == sha:
            ok += 1
            log("OK    %s %s (%d bytes)" % (sha, how, len(data)))
        else:
            bad += 1
            log("BAD   %s -> %s" % (sha, got))
    left = len([s for s in todo if not present(s)])
    log("--- round done ok=%d bad=%d remaining=%d ---" % (ok, bad, left))


if __name__ == "__main__":
    main()
