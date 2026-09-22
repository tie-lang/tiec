"""通用整函数分片器 v5：**命名空间感知** + 不覆盖既有分片 + 完整性校验。

用法：python split_parts5.py plan|apply <rel-path> [budget]
环境：TIE_SPLIT_EXCLUDE=逗号分隔的函数名（不搬）

v5 相对 v4 的关键修正（实测踩坑）：
  * 文件里 `namespace X {` 之前定义的函数是**顶层函数**，跨 ns 裸名调用依赖它保持
    顶层身份（如 semantic.tie 的 sm_warn_add 被 namespace scheck 裸调）。分片必须
    按函数各自的命名空间上下文包裹：顶层函数不包 ns，ns 内函数包 `namespace X {`，
    上下文变化处开新块。
  * 分片文件名用 `_qN`，绝不覆盖既有 `_pN`（曾因覆盖丢失已搬出的函数定义）。
  * 结束打印函数集完整性校验（前集必须 ⊆ 后集）。
"""
import io
import os
import re
import sys

# 仓库根：环境变量 TIEC_ROOT 优先，其次当前工作目录（原脚本写死本机绝对路径）
ROOT = os.environ.get("TIEC_ROOT") or os.getcwd()
EXCLUDE = set((os.environ.get("TIE_SPLIT_EXCLUDE") or "").split(",")) - {""}


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


def brace_end(lines, i):
    d = 0
    j = i
    while j < len(lines):
        d += line_delta(lines[j])
        if j > i and d == 0:
            return j
        j += 1
    return len(lines) - 1


def funcs(lines):
    out = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)(pub )?func ([A-Za-z_][A-Za-z_0-9]*)\s*\(", lines[i])
        if m:
            j = brace_end(lines, i)
            k = i - 1
            while k >= 0 and lines[k].lstrip().startswith("//"):
                k -= 1
            out.append((m.group(3), k + 1, j, len(m.group(1))))
            i = j + 1
            continue
        i += 1
    return out


def ns_of(lines, idx):
    """向上找该行所属命名空间（brace 深度未闭合的最近 namespace）。"""
    depth = 0
    i = idx

    def stack_at(k):
        s = []
        for t in range(k + 1):
            m = re.match(r"^\s*namespace\s+([A-Za-z_][A-Za-z_0-9]*)", lines[t])
            if m:
                s.append((m.group(1), t))
        return s

    opens = []
    for t in range(idx + 1):
        m = re.match(r"^\s*namespace\s+([A-Za-z_][A-Za-z_0-9]*)", lines[t])
        if m:
            opens.append(t)
    # 从最近的 namespace 行起算，若其块在 idx 之前已闭合则不属于该 ns
    for t in reversed(opens):
        d = 0
        for u in range(t, idx + 1):
            d += line_delta(lines[u])
        if d > 0:
            return re.match(r"^\s*namespace\s+([A-Za-z_][A-Za-z_0-9]*)", lines[t]).group(1)
    return None


def do(path, budget, apply_):
    lines = read(path)
    base = os.path.basename(path)[:-4]
    fs = [f for f in funcs(lines) if f[0] not in EXCLUDE]
    if not fs:
        print("%s: 无函数，跳过" % base)
        return
    ctx = {nm: ns_of(lines, a) for nm, a, b, ind in fs}
    parts, cur, cur_len = [], [], 0
    for nm, a, b, ind in fs:
        ln = b - a + 1
        if cur and cur_len + ln > budget:
            parts.append(cur)
            cur, cur_len = [], 0
        cur.append((nm, a, b))
        cur_len += ln
    if cur:
        parts.append(cur)
    print("%s: 函数 %d，分 %d 片（顶层 %d / ns 内 %d）"
          % (base, len(fs), len(parts),
             sum(1 for f in fs if ctx[f[0]] is None),
             sum(1 for f in fs if ctx[f[0]] is not None)))
    for i, arr in enumerate(parts, 1):
        print("   _q%d: 函数 %2d 行 %5d（%s…%s）  ns=%s"
              % (i, len(arr), sum(b - a + 1 for _, a, b in arr), arr[0][0], arr[-1][0],
                 {ctx[n] for n, _, _ in arr}))
    if not apply_:
        return
    moved, names = set(), []
    for idx, arr in enumerate(parts, 1):
        out = ["type tie<class>",
               "// compiler/%s_q%d.tie —— 分片 %d（p.9.21.3 单文件 ≤800 行）"
               % (os.path.relpath(path, os.path.join(ROOT, "compiler")).replace("\\", "/")[:-4], idx, idx),
               "// ============================================================",
               "// 只搬函数与紧邻注释；顶层全局 var 与 import 树仍留在 %s.tie。" % base,
               "// 顶层函数保持顶层身份（跨 ns 裸调依赖），ns 内函数按上下文包 namespace。"]
        open_ns = None
        for nm, a, b in arr:
            c = ctx[nm]
            if c != open_ns:
                if open_ns is not None:
                    out.append("}")
                if c is not None:
                    out.append("namespace %s {" % c)
                open_ns = c
            ind = 0
            body = [(l[ind:] if ind and l.startswith(" " * ind) else l) for l in lines[a:b + 1]]
            out.append("\n".join(body))
            out.append("")
            moved.add(nm)
            names.append(nm)
        if open_ns is not None:
            out.append("}")
        fp = os.path.join(os.path.dirname(path), "%s_q%d.tie" % (base, idx))
        with io.open(fp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(out))
        print("[写出] %s" % os.path.basename(fp))
    drop = set()
    for nm, a, b, ind in fs:
        if nm in moved:
            for k in range(a, b + 1):
                drop.add(k)
    kept = [ln for i, ln in enumerate(lines) if i not in drop]
    cleaned, blank = [], 0
    for ln in kept:
        if ln.strip() == "":
            blank += 1
            if blank > 2:
                continue
        else:
            blank = 0
        cleaned.append(ln)
    news = ['import "./%s_q%d.tie"' % (base, i) for i in range(1, len(parts) + 1)]
    first_func = next((i for i, ln in enumerate(cleaned)
                       if re.match(r"^\s*(?:pub )?func ", ln)), len(cleaned))
    cleaned = cleaned[:first_func] + news + [""] + cleaned[first_func:]
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(cleaned))
    # 完整性校验
    import glob as _glob

    def _names(txt):
        return set(re.findall(r"^\s*(?:pub\s+)?func\s+([A-Za-z_][A-Za-z_0-9]*)", txt, flags=re.M))

    before = _names("\n".join(lines))
    after = _names("\n".join(cleaned))
    for fp in _glob.glob(os.path.join(os.path.dirname(path), "%s_[pq]*.tie" % base)):
        after |= _names(io.open(fp, encoding="utf-8").read())
    print("[校验] 函数集 前=%d 后=%d 丢失=%s"
          % (len(before), len(after), sorted(before - after) or "无"))
    print("[更新] %s（%d 行）" % (os.path.basename(path), len(cleaned)))


if __name__ == "__main__":
    mode, rel = sys.argv[1], sys.argv[2]
    budget = int(sys.argv[3]) if len(sys.argv) > 3 else 700
    p = os.path.join(ROOT, "compiler", rel.replace("/", os.sep)) + ("" if rel.endswith(".tie") else ".tie")
    do(p, budget, mode == "apply")
