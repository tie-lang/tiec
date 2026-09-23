# -*- coding: utf-8 -*-
"""Namespace visibility survey for the tiec dogfood (p.9.21.4 / II1 diagnosis).

tie already enforces ns-private functions (A1b) as an error: sstate.check_visibility
rejects a non-pub namespace function called from outside its namespace (sub-namespaces
count as inside), while top-level functions (no "::" in the full name) stay open.
This is the survey the design asks for before touching the ladder: per namespace,
how many functions are pub (the API surface) vs private, plus how many functions
live at top level where the guard does not apply.

Namespace attribution reuses the same backward scan as the splitting tools
(function -> nearest enclosing unclosed `namespace`), which is verified by the
G1/G2 work; a per-line brace-depth stack is not, because tie sources carry
irregular indentation and zero-indent `if` arms.

usage: python visibility_survey.py [repo-root]
"""
import io
import os
import re
import sys
from collections import defaultdict

ROOT = sys.argv[1] if len(sys.argv) > 1 else (os.environ.get("TIEC_ROOT") or os.getcwd())
SKIP = ("_bak", "proto", "backuptmp", "tests")
FUNC_RE = re.compile(r"^(\s*)(pub\s+)?func\s+([A-Za-z_][A-Za-z_0-9]*)")
NS_RE = re.compile(r"^\s*namespace\s+([A-Za-z_][A-Za-z_0-9]*)")


def line_delta(ln):
    d = 0
    i = 0
    in_str = False
    while i < len(ln):
        c = ln[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == "/" and i + 1 < len(ln) and ln[i + 1] == "/":
            break
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
        i += 1
    return d


def block_end(lines, i):
    d = 0
    seen = False
    j = i
    while j < len(lines):
        ln = lines[j]
        d += line_delta(ln)
        if "{" in ln.split("//")[0]:
            seen = True
        if seen and d == 0 and not re.search(r"\}\s*else\b", ln.split("//")[0]):
            return j
        j += 1
    return len(lines) - 1


def ns_of(lines, idx):
    opens = [t for t in range(idx + 1) if NS_RE.match(lines[t])]
    for t in reversed(opens):
        d = 0
        for u in range(t, idx + 1):
            d += line_delta(lines[u])
        if d > 0:
            return NS_RE.match(lines[t]).group(1)
    return None


def sources():
    out = []
    for dp, dn, fns in os.walk(os.path.join(ROOT, "compiler")):
        if any(s in dp for s in SKIP):
            continue
        for fn in fns:
            if fn.endswith(".tie") and not fn.startswith("_") and not fn.startswith("README"):
                out.append(os.path.join(dp, fn))
    return sorted(out)


def main():
    stats = defaultdict(lambda: [0, 0])
    total_top = 0
    for path in sources():
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
        i = 0
        n = len(lines)
        while i < n:
            m = FUNC_RE.match(lines[i])
            if not m:
                i += 1
                continue
            e = block_end(lines, i)
            ns = ns_of(lines, i)
            if ns is None:
                total_top += 1
            else:
                if m.group(2):
                    stats[ns][0] += 1
                else:
                    stats[ns][1] += 1
            i = e + 1

    rows = sorted(stats.items())
    tp = sum(p for _, (p, _) in rows)
    tv = sum(v for _, (_, v) in rows)
    print("%-24s %6s %8s" % ("namespace", "pub", "private"))
    for ns, (p, v) in rows:
        print("%-24s %6d %8d" % (ns, p, v))
    print("--- %d namespaces, %d ns functions (pub %d / private %d), %d top-level (guard exempt) ---"
          % (len(rows), tp, tp, tv, total_top))


main()
