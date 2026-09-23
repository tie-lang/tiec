# -*- coding: utf-8 -*-
"""Find compiler sources that nothing imports (p.9.21 G8 orphan detection).

usage: python orphan_check.py [repo-root]

Reports every .tie file under compiler/ that is not the target of any
`import "./..."` in another file. Entry points and standalone self-tests are
expected to appear here; anything else is a leftover from an earlier split pass
(for example the `_pN` shards superseded by the `_qN` ones).

Note: this is a report only. Deleting anything is a separate decision.
"""
import io
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else (os.environ.get("TIEC_ROOT") or os.getcwd())
SKIP = ("_bak", "proto", "backuptmp")
IMPORT_RE = re.compile(r'^\s*import\s+"\./([^"]+)"', re.M)


def norm(p):
    return os.path.normcase(os.path.normpath(os.path.abspath(p)))


def sources():
    out = []
    for dp, dn, fns in os.walk(os.path.join(ROOT, "compiler")):
        if any(s in dp for s in SKIP):
            continue
        for fn in fns:
            if fn.endswith(".tie"):
                out.append(os.path.join(dp, fn))
    return sorted(out)


def imported():
    out = set()
    for p in sources():
        try:
            with io.open(p, encoding="utf-8", errors="replace") as fh:
                txt = fh.read()
        except OSError:
            continue
        for m in IMPORT_RE.finditer(txt):
            out.add(norm(os.path.join(os.path.dirname(p), m.group(1))))
    return out


def main():
    files = sources()
    imp = imported()
    orph = [f for f in files if norm(f) not in imp]
    print("%d source files, %d not imported by anything:" % (len(files), len(orph)))
    for f in orph:
        with io.open(f, encoding="utf-8", errors="replace") as fh:
            n = len(fh.read().split("\n"))
        print("  %5d  %s" % (n, os.path.relpath(f, ROOT).replace("\\", "/")))


main()
