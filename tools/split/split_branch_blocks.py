# -*- coding: utf-8 -*-
"""Generic `if <COND> { ... }` branch extractor (p.9.21 G2: single function <=300 lines).

Turns a flat dispatcher made of independent `if <cond> { ... }` statements into
one extracted function per branch, leaving the dispatcher as a one-line-per-branch
skeleton. This is the statement-level counterpart of split_dispatch.py, which only
handles `if <VAR> == <int literal>` chains.

usage: python split_branch_blocks.py plan|apply <rel-path-under-compiler> <func>
       python split_branch_blocks.py plan|apply <rel-path> <func> <prefix> <budget>
env:   TIEC_ROOT repo root (default cwd)

Safety rules (learned the hard way, see tools/README.md):
  * brace counting is string/comment aware - `{` appears inside tie strings
  * an `} else if` / `} else {` tail belongs to the same block and moves with it
  * a branch is only extracted when its last top-level statement is a `return`
    (otherwise the fall-through to the next branch would be lost)
  * a branch is not extracted when a local it declares is referenced outside it,
    nor when it reads a local declared by a sibling statement
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
    """Net brace delta of a line, ignoring strings, comments and chars."""
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
    """Index of the line closing the block opened on line i."""
    d = 0
    j = i
    while j < len(lines):
        d += line_delta(lines[j])
        if j >= i and d == 0:
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
    """Blank out string contents and trailing comments; keep column positions.

    Needed because `{k: v}` inside a message string otherwise looks exactly like
    a reference to a local named `k`.
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
    """Identifiers actually *referenced*: skips comments, strings and `ns.member` tails."""
    out = []
    for ln in body:
        s = ln.strip()
        if s.startswith("//"):
            continue
        ln = strip_literals(ln)
        for m in IDENT.finditer(ln):
            if m.start() > 0 and ln[m.start() - 1] == ".":
                continue
            out.append(m.group(0))
    return out


def decls(body, indent=None):
    """Local names declared by `var x` / `var (a, b) = ...` anywhere in body."""
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


def main():
    rel = sys.argv[2]
    fname = sys.argv[3]
    prefix = sys.argv[4] if len(sys.argv) > 4 else fname + "_"
    budget = int(sys.argv[5]) if len(sys.argv) > 5 else 600
    path = os.path.join(ROOT, "compiler", rel.replace("/", os.sep))
    lines = read(path)
    a, b = find_func(lines, fname)
    if a < 0:
        print("function %s not found" % fname)
        return
    ns = ns_of(lines, a)
    # Reuse the dispatcher's own signature: the extracted branch functions take
    # the same parameters (`s`, not a hardcoded `id`) and return the same type.
    sig = re.match(r"^\s*(?:pub )?func %s\s*\(([^)]*)\)\s*(->\s*[^ ]+)?\s*\{" % re.escape(fname),
                   lines[a])
    params = (sig.group(1) or "").strip() if sig else "id: i64"
    ret = (sig.group(2) or "-> i64").strip() if sig else "-> i64"
    args = ", ".join(p.split(":")[0].strip().split("(")[-1]
                     for p in params.split(",") if p.strip())
    ind = len(lines[a]) - len(lines[a].lstrip())
    body_ind = ind + 4
    outer_ind = " " * ind

    # --- collect top-level items of the function body -----------------------
    items = []  # (kind, start, end) kind in {if, other}; end inclusive
    i = a + 1
    while i < b:
        s = lines[i].strip()
        if s == "" or s.startswith("//"):
            i += 1
            continue
        if re.match(r"^%sif " % (" " * body_ind), lines[i]):
            e = block_end(lines, i)
            # swallow `} else if ... {` / `} else {` tails
            while e + 1 < b and re.match(r"^%s\}\s*else" % (" " * body_ind), lines[e + 1]):
                e = block_end(lines, e + 1)
            # leading comments
            st = i - 1
            while st > a and lines[st].strip().startswith("//"):
                st -= 1
            items.append(("if", st + 1, e))
            i = e + 1
            continue
        items.append(("other", i, i))
        i += 1

    # --- locals declared outside any if-block -------------------------------
    # The prologue `var` lines are re-emitted inside every extracted function,
    # so reading them is fine; only *later* sibling declarations are a problem.
    prologue = []
    outer_vars = set()
    for kind, s, e in items:
        if kind == "other":
            for ln in lines[s:e + 1]:
                if re.match(r"^%svar " % (" " * body_ind), ln):
                    prologue.append(ln)
            outer_vars |= decls(lines[s:e + 1], body_ind)
    prologue_vars = set()
    for ln in prologue:
        m = re.match(r"^%svar ([A-Za-z_][A-Za-z_0-9]*)" % (" " * body_ind), ln)
        if m:
            prologue_vars.add(m.group(1))
    outer_vars -= prologue_vars

    # --- decide which if-blocks can be extracted ----------------------------
    cand = []
    skipped = []
    for idx, (kind, s, e) in enumerate(items):
        if kind != "if":
            continue
        body = lines[s + 1:e]  # inside the braces
        inner = decls(body)
        # last top-level statement of the body must be a return
        last = None
        for ln in reversed(body):
            if ln.strip() == "" or ln.strip().startswith("//"):
                continue
            last = ln
            break
        if last is None or not re.match(r"^%sreturn" % (" " * (body_ind + 4)), last):
            skipped.append((s, "尾部非 return（可能贯穿到下一分支）"))
            continue
        used = set(words(body))
        # must not read a local declared by a *later* sibling statement
        if (used & outer_vars) - inner:
            skipped.append((s, "读取兄弟语句声明的局部: %s"
                            % sorted((used & outer_vars) - inner)))
            continue
        # locals it declares must not be read outside it, unless re-declared there
        rest = []
        for j, (k2, s2, e2) in enumerate(items):
            if j == idx:
                continue
            rest.extend(lines[s2:e2 + 1])
        leak = set()
        for j, (k2, s2, e2) in enumerate(items):
            if j == idx:
                continue
            blk = lines[s2:e2 + 1]
            leak |= (inner & set(words(blk))) - decls(blk)
        if leak:
            skipped.append((s, "局部被外部读取: %s" % sorted(leak)))
            continue
        cand.append((s, e, _if_line(lines, s, e)))

    nbranch = sum(1 for k, _, _ in items if k == "if")
    print("%s: 函数体 %d 行，分支 %d 个，可提取 %d 个（ns=%s）"
          % (fname, b - a + 1, nbranch, len(cand), ns))
    if sys.argv[1] != "apply":
        for s, e, il in cand:
            print("   %-28s %4d 行  %s" % (_slug(lines[il], prefix), e - s + 1,
                                           lines[il].strip()[:60]))
        for s, why in skipped:
            print("   [跳过] %s  %s" % (lines[s].strip()[:52], why))
        return

    # --- build replacements -------------------------------------------------
    # Each candidate keeps its leading comments, and the `if ... { ... }` span is
    # rewritten as a one-line dispatch. Replacements are applied while walking the
    # line list (writing into `lines` first and then filtering by index would drop
    # the freshly written dispatch line, since its index lies inside the span).
    repl = {}
    news = []
    for s, e, il in cand:
        cond = lines[il].strip()
        slug = _slug(lines[il], prefix)
        body = lines[il + 1:e]
        fn = ["%spub func %s(%s) %s {" % (outer_ind, slug, params, ret)]
        fn.extend(prologue)
        fn.extend(body)
        fn.append("%s}" % outer_ind)
        repl[il] = e, [
            "%s    if %s {" % (outer_ind, _cond_body(cond)),
            "%s        return %s(%s)" % (outer_ind, slug, args),
            "%s    }" % outer_ind,
        ]
        news.append((slug, fn))

    kept = []
    i = 0
    while i < len(lines):
        if i in repl:
            end, new = repl[i]
            kept.extend(new)
            i = end + 1
            continue
        kept.append(lines[i])
        i += 1

    # emit extracted functions into shards
    shards, cur, cur_len = [], [], 0
    for slug, fn in news:
        if cur and cur_len + len(fn) + 1 > budget:
            shards.append(cur)
            cur, cur_len = [], 0
        cur.append((slug, fn))
        cur_len += len(fn) + 1
    if cur:
        shards.append(cur)
    base = sys.argv[6] if len(sys.argv) > 6 else os.path.basename(path)[:-4]
    for n, arr in enumerate(shards, 1):
        out = ["type tie<class>",
               "// compiler/frontend/%s_ie%d.tie —— %s 分支提子函数分片 %d（p.9.21 G2 单函数 ≤300 行）"
               % (base, n, fname, n),
               "// ============================================================",
               "// 只含函数与注释：import 树与顶层全局 var 仍留在原主文件；",
               "// 分片内函数与原调度器同 namespace，跨文件裸名互调。"]
        if ns:
            out.append("namespace %s {" % ns)
        for slug, fn in arr:
            out.append("\n".join(fn))
            out.append("")
        if ns:
            out.append("}")
        fp = os.path.join(os.path.dirname(path), "%s_ie%d.tie" % (base, n))
        with io.open(fp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(out))
        print("[写出] %s（%d 函数 / %d 行）"
              % (os.path.basename(fp), len(arr), len("\n".join(out).split("\n"))))

    imports = ['import "./%s_ie%d.tie"' % (base, i) for i in range(1, len(shards) + 1)]
    # Imports must sit at file top level: a namespace body only admits functions,
    # classes and nested namespaces (E00449), so the insertion point is before the
    # first `namespace` line rather than before the first function.
    first_ns = next((i for i, ln in enumerate(kept)
                     if re.match(r"^\s*namespace ", ln)), len(kept))
    first_fn = next((i for i, ln in enumerate(kept)
                     if re.match(r"^\s*(?:pub )?func ", ln)), len(kept))
    first = min(first_ns, first_fn)
    kept = kept[:first] + imports + [""] + kept[first:]
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(kept))
    print("[更新] %s（%d 行）" % (os.path.basename(path), len(kept)))


def _if_line(lines, s, e):
    """Index of the `if ... {` line inside the item [s, e]."""
    for i in range(s, e + 1):
        if re.match(r"^\s*if ", lines[i]):
            return i
    return s


def _cond_body(cond):
    """`if tag == N_CALL {` -> `tag == N_CALL`"""
    c = cond
    if c.startswith("if "):
        c = c[3:]
    if c.endswith("{"):
        c = c[:-1]
    return c.strip()


def _slug(cond_line, prefix):
    c = _cond_body(cond_line)
    m = re.search(r"==\s*([A-Za-z_][A-Za-z_0-9]*|[0-9]+)", c)
    tok = m.group(1) if m else "x"
    if tok.isdigit():
        tok = "tag" + tok
    tok = re.sub(r"^N_|^S_N_", "", tok)
    return (prefix + tok).lower()


main()
