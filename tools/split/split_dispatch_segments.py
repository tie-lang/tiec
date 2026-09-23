# -*- coding: utf-8 -*-
"""Dispatch-chain segmenter (p.9.21 G2: single function <=300 lines).

For a function whose body is a long chain of `if <cond> { ... }` tests where a
well-known sentinel value means "no branch matched" (builtin_expr: -1), cut the
chain into consecutive segments, move each segment into its own function, and
leave the original as a short runner:

    func builtin_expr(nm: string, id: i64) -> i64 {
        var r: i64 = 0
        r = builtin_expr_seg1(nm, id)
        if r != -1 { return r }
        r = builtin_expr_seg2(nm, id)
        if r != -1 { return r }
        return -1  // non-builtin
    }

Correctness relies on the sentinel being unambiguous: a branch that matched and
failed still returns the sentinel, and the later segments cannot match that name
again, so the final result is unchanged - only extra comparisons are paid.

usage: python split_dispatch_segments.py plan|apply <rel-under-compiler> <func> <prefix> <budget> [shardbase]
env:   TIEC_ROOT repo root (default cwd)
"""
import io
import os
import re
import sys

ROOT = os.environ.get("TIEC_ROOT") or os.getcwd()
IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")


def read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read().split("\n")


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


def has_open_brace(ln):
    return "{" in strip_literals(ln)


def block_end(lines, i):
    """Line closing the block opened at/after line i.

    A multi-line `if` condition has balanced braces on its own first lines, so
    "delta back to zero" alone would stop there; only start closing once a `{`
    has actually been seen.
    """
    d = 0
    seen_open = False
    j = i
    while j < len(lines):
        ln = strip_literals(lines[j])
        d += line_delta(lines[j])
        if "{" in ln:
            seen_open = True
        # A `} else if ...` line closes the previous arm, so the running depth can
        # hit zero in the middle of a chain (and mid-condition when the condition
        # continues on the next line). The chain is one logical block, so such a
        # line never ends it.
        if seen_open and d == 0 and not re.search(r"\}\s*else\b", ln):
            return j
        j += 1
    return len(lines) - 1


def find_func(lines, name):
    for i, ln in enumerate(lines):
        if re.match(r"^\s*(?:pub )?func %s\s*\(" % re.escape(name), ln):
            return i, block_end(lines, i)
    return -1, -1


def ns_of(lines, idx):
    opens = [t for t in range(idx + 1)
             if re.match(r"^\s*namespace\s+[A-Za-z_][A-Za-z_0-9]*", lines[t])]
    for t in reversed(opens):
        d = 0
        for u in range(t, idx + 1):
            d += line_delta(lines[u])
        if d > 0:
            return re.match(r"^\s*namespace\s+([A-Za-z_][A-Za-z_0-9]*)", lines[t]).group(1)
    return None


def strip_literals(ln):
    """Blank out string contents and trailing comments, keeping columns.

    Message text like `{k: v}` must not look like a reference to a local `k`,
    and `types.is_map` must not look like a reference to a local `is_map`.
    """
    out = []
    in_str = False
    i = 0
    while i < len(ln):
        c = ln[i]
        if in_str:
            if c == "\\":
                out.append("  ")
                i += 2
                continue
            if c == '"':
                in_str = False
                out.append(c)
                i += 1
                continue
            out.append(" ")
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < len(ln) and ln[i + 1] == "/":
            break
        out.append(c)
        i += 1
    return "".join(out)


def words(body):
    out = []
    for ln in body:
        if ln.strip().startswith("//"):
            continue
        ln = strip_literals(ln)
        for m in IDENT.finditer(ln):
            if m.start() > 0 and ln[m.start() - 1] == ".":
                continue
            out.append(m.group(0))
    return out


def decls(body):
    out = set()
    for ln in body:
        m = re.match(r"^\s*var ([A-Za-z_][A-Za-z_0-9]*)", ln)
        if m:
            out.add(m.group(1))
            continue
        m = re.match(r"^\s*var \(([^)]*)\)", ln)
        if m:
            for part in m.group(1).split(","):
                p = part.strip()
                if re.match(r"^[A-Za-z_][A-Za-z_0-9]*$", p):
                    out.add(p)
    return out


def groups(items, lines):
    """Merge items that share locals into atomic groups.

    A cut between two items is only safe when neither reads a local the other
    declares; otherwise the segment boundary moves the declaration away from its
    use. Union-find over items, then pack whole groups.
    """
    n = len(items)
    toks = [set(words(lines[s:e + 1])) for s, e in items]
    decl = [decls(lines[s:e + 1]) for s, e in items]
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    for i in range(n):
        for j in range(i + 1, n):
            if (decl[i] & toks[j]) - decl[j] or (decl[j] & toks[i]) - decl[i]:
                union(i, j)
    merged = {}
    for i in range(n):
        merged.setdefault(find(i), []).append(items[i])
    return [merged[k] for k in sorted(merged, key=lambda k: merged[k][0][0])]


def top_items(lines, a, b, body_ind):
    """Top-level statements of a function body, indentation-agnostic.

    The original plan keyed items off a fixed body indent, but some sources (the
    as_* chain in irgen_dispatch.tie) carry zero-indented `if` lines inside a
    4-space body, so those lines were misread as one-line statements and their
    bodies were torn apart. Items are now delimited by brace depth: a statement
    starts wherever the running depth is zero, and ends where it returns to zero.
    """
    items = []
    i = a + 1
    while i < b:
        st = lines[i].strip()
        if st == "" or st.startswith("//"):
            i += 1
            continue
        # A control keyword may open its brace on a later line (multi-line
        # condition), so those go through block_end even without a `{` here.
        ctrl = re.match(r"^\s*(if|while|for|else|unsafe|switch)\b", lines[i])
        if not ctrl and "{" not in strip_literals(lines[i]):
            # brace-free plain statement (var/return/expression): one item
            items.append((i, i))
            i += 1
            continue
        if re.match(r"^\s*(if|while|for|else|unsafe|switch)\b", lines[i]):
            e = block_end(lines, i)
            while e + 1 < b and re.match(r"^\s*\}\s*else", lines[e + 1]):
                e = block_end(lines, e + 1)
            st2 = i - 1
            while st2 > a and lines[st2].strip().startswith("//"):
                st2 -= 1
            items.append((st2 + 1, e))
            i = e + 1
            continue
        items.append((i, block_end(lines, i)))
        i += 1
    return items


def main():
    mode, rel, fname, prefix, budget = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
    shardbase = sys.argv[6] if len(sys.argv) > 6 else (fname + "_seg")
    path = os.path.join(ROOT, "compiler", rel.replace("/", os.sep))
    lines = read(path)
    a, b = find_func(lines, fname)
    if a < 0:
        print("function %s not found" % fname)
        return
    ns = ns_of(lines, a)
    sig = re.match(r"^\s*((?:pub )?)func %s\s*\(([^)]*)\)\s*(->\s*[^ ]+)?\s*\{" % re.escape(fname),
                   lines[a])
    vis = sig.group(1) or ""
    params = (sig.group(2) or "").strip()
    ret = (sig.group(3) or "-> i64").strip()
    args = ", ".join(p.split(":")[0].strip().split("(")[-1] for p in params.split(",") if p.strip())
    body_ind = (len(lines[a]) - len(lines[a].lstrip())) + 4
    pad = " " * (body_ind - 4)

    # ---- collect top-level items of the body --------------------------------
    items = top_items(lines, a, b, body_ind)

    # the trailing "nothing matched" tail stays in the runner: it is usually more
    # than one line (set g_err, then return the sentinel), so take everything
    # after the last dispatch branch rather than just a final `return`.
    tail = None
    last_if = -1
    for n, (s, e) in enumerate(items):
        # items carry their leading comments, so look at the first code line
        k = s
        while k < e and (lines[k].strip() == "" or lines[k].strip().startswith("//")):
            k += 1
        if re.match(r"^\s*if\b", lines[k]):
            last_if = n
    if 0 <= last_if < len(items) - 1:
        tail = items[last_if + 1:]
        items = items[:last_if + 1]

    # ---- pack into segments, keeping local-variable groups atomic ------------
    atomic = groups(items, lines)
    segs, cur, curlen = [], [], 0
    for grp in atomic:
        ln = sum(e - s + 1 for s, e in grp)
        if cur and curlen + ln > budget:
            segs.append(cur)
            cur, curlen = [], 0
        cur.extend(grp)
        curlen += ln
    if cur:
        segs.append(cur)

    total = sum(e - s + 1 for s, e in items)
    print("%s: 函数体 %d 行，项 %d 个，分 %d 段（ns=%s，尾句=%s）"
          % (fname, b - a + 1, len(items), len(segs), ns, "保留" if tail else "无"))
    if mode != "apply":
        for n, arr in enumerate(segs, 1):
            print("   seg%d: %4d 行  %s … %s" % (n, sum(e - s + 1 for s, e in arr),
                                                 lines[arr[0][0]].strip()[:40],
                                                 lines[arr[-1][1]].strip()[:40]))
        return

    # ---- write segment files ------------------------------------------------
    seg_names = []
    for n, arr in enumerate(segs, 1):
        seg_names.append("%sseg%d" % (prefix, n))
        out = ["type tie<class>",
               "// compiler/%s/%s%d.tie —— %s 分派链分段 %d（p.9.21 G2 单函数 ≤300 行）"
               % (os.path.relpath(os.path.dirname(path), os.path.join(ROOT, "compiler")).replace("\\", "/"),
                  shardbase, n, fname, n),
               "// ============================================================",
               "// 只含函数与注释：import 树与顶层全局 var 仍留在原主文件；",
               "// 与原函数同 namespace，跨文件裸名互调；段尾 return <sentinel> = 本段未命中。"]
        if ns:
            out.append("namespace %s {" % ns)
        out.append("%sfunc %sseg%d(%s) %s {" % (pad, prefix, n, params, ret))
        for s, e in arr:
            out.extend(lines[s:e + 1])
        out.append("%s    return -1  // 本段未命中" % pad)
        out.append("%s}" % pad)
        if ns:
            out.append("}")
        fp = os.path.join(os.path.dirname(path), "%s%d.tie" % (shardbase, n))
        with io.open(fp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(out))
        print("[写出] %s（%d 项 / %d 行）"
              % (os.path.basename(fp), len(arr), len("\n".join(out).split("\n"))))

    # ---- rewrite the runner -------------------------------------------------
    drop = set()
    for s, e in items:
        for k in range(s, e + 1):
            drop.add(k)
    runner = []
    runner.append("%s    var r: i64 = 0" % pad)
    for nm_ in seg_names:
        runner.append("%s    r = %s(%s)" % (pad, nm_, args))
        runner.append("%s    if r != -1 {" % pad)
        runner.append("%s        return r" % pad)
        runner.append("%s    }" % pad)
    if tail:
        for s, e in tail:
            for k in range(s, e + 1):
                pass
        runner.extend(ln for s, e in tail for ln in lines[s:e + 1])
    else:
        runner.append("%s    return -1" % pad)
    kept = []
    for idx, ln in enumerate(lines):
        if idx == a + 1:
            kept.extend(runner)
        if idx in drop:
            continue
        kept.append(ln)
    imports = ['import "./%s%d.tie"' % (shardbase, n) for n in range(1, len(segs) + 1)]
    first_ns = next((i for i, ln in enumerate(kept) if re.match(r"^\s*namespace ", ln)), len(kept))
    first_fn = next((i for i, ln in enumerate(kept)
                     if re.match(r"^\s*(?:pub )?func ", ln)), len(kept))
    first = min(first_ns, first_fn)
    kept = kept[:first] + imports + [""] + kept[first:]
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(kept))
    print("[更新] %s（%d 行）" % (os.path.basename(path), len(kept)))


main()
