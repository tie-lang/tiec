# -*- coding: utf-8 -*-
"""Function length auditor (p.9.21 G2: single function <=300 lines).

usage: python func_len.py [repo-root] [limit]
Prints every function longer than the limit as `<lines> <file> <func>`.

Brace counting is string/comment aware, so `{` inside strings or comments does
not open a block.
"""
import io
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else (os.environ.get("TIEC_ROOT") or os.getcwd())
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 300
SKIP_DIR = ("_bak", "proto", "backuptmp", "_ghidra_out", "_m6_out", "node_modules")


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


def scan(path):
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")
    out = []
    i = 0
    while i < len(lines):
        m = re.match(r"^\s*(?:pub )?func ([A-Za-z_][A-Za-z_0-9]*)\s*\(", lines[i])
        if not m:
            i += 1
            continue
        d = 0
        j = i
        while j < len(lines):
            d += line_delta(lines[j])
            if j >= i and d == 0:
                break
            j += 1
        if j - i + 1 > LIMIT:
            out.append((j - i + 1, path, m.group(1)))
        i = j + 1
    return out


def main():
    hits = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "compiler")):
        dirnames[:] = [d for d in dirnames if not any(s in d for s in SKIP_DIR)]
        for fn in filenames:
            if not fn.endswith(".tie") or fn.startswith("_") or fn.startswith("README"):
                continue
            hits.extend(scan(os.path.join(dirpath, fn)))
    hits.sort(reverse=True)
    for n, p, f in hits:
        print("%5d  %-46s %s" % (n, os.path.relpath(p, ROOT).replace("\\", "/"), f))
    print("--- %d function(s) over %d lines ---" % (len(hits), LIMIT))


main()
