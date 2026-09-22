"""通用「调度器分支提取器」：把 `if <VAR> == <整数字面量> { ... }` 形态的巨型
调度函数按分支提为独立函数（p.9.21.3 函数级拆解）。

用法：
  python split_dispatch.py plan  <rel-path> <func> <VAR> <out-file>
  python split_dispatch.py apply <rel-path> <func> <VAR> <out-file>

例：
  split_dispatch.py apply backend/irgen_stmt.tie tig_stmt tag irgen_stmt_gen.tie
  split_dispatch.py apply backend/llvmgen_inst.tie gen_inst op llvmgen_inst_gen.tie

要点：
  * 分支 = 从 `    if <VAR> == N {` 到其匹配闭合括号（字符串/注释感知计数）；
  * 提取体保留整块（含闭括号），函数名 `<前缀>_<N>[_<slug>]`（slug 取块内首条
    注释的首个 ASCII 标识符）；
  * 调度器原地收敛为一行一分支；返回 i64 的函数用 `return f(id)`，void 函数
    用 `f(id)` + `return`（后续分支不可能再命中，语义等价）；
  * 分支体内引用 <VAR> 时该提取函数额外带 <VAR> 形参。
"""
import io
import os
import re
import sys

# 仓库根：环境变量 TIEC_ROOT 优先，其次当前工作目录（原脚本写死本机绝对路径）
ROOT = os.environ.get("TIEC_ROOT") or os.getcwd()


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


def block_end(lines, start, limit):
    d = 0
    j = start
    while j < limit:
        d += line_delta(lines[j])
        if d <= 0 and j > start:
            return j
        j += 1
    return limit


def find_func(lines, name):
    for i, ln in enumerate(lines):
        if re.match(r"^\s*(?:pub\s+)?func %s\s*\(" % re.escape(name), ln):
            return i, block_end(lines, i, len(lines))
    raise SystemExit("未找到函数 %s" % name)


def ns_name(lines):
    for ln in lines:
        m = re.match(r"^\s*namespace\s+([A-Za-z_][A-Za-z_0-9]*)", ln)
        if m:
            return m.group(1)
    return None


def analyze(path, func, var):
    lines = read(path)
    s, e = find_func(lines, func)
    ret_i64 = "-> i64" in lines[s]
    sig = lines[s]
    sig = sig[:sig.rfind(")")] if ")" in sig else sig
    inner = sig[sig.find("(") + 1:]
    params = []
    for part in inner.split(","):
        mm = re.match(r"\s*([A-Za-z_][A-Za-z_0-9]*)\s*:\s*(.+?)\s*$", part)
        if mm:
            params.append((mm.group(1), mm.group(2)))
    pname = params[0][0] if params else "id"
    extra = [x for x in params if x[0] != var]
    blocks = []
    others = []
    pat = re.compile(r'^    if (?:(?:%s) == (?:\d+|")|\((?:%s) == )' % (re.escape(var), re.escape(var)))
    i = s + 1
    while i < e:
        if pat.match(lines[i]):
            # 条件可能跨多行：向后扫到含 `{` 的行为止，条件文本合并为单行
            k = i
            while k <= e and "{" not in lines[k]:
                k += 1
            j = block_end(lines, k, e + 1)
            cond = " ".join(l.strip() for l in lines[i:k + 1])
            cond = cond[3:cond.rfind("{")].strip()
            slug = ""
            for q in range(i + 1, min(i + 5, j + 1)):
                m = re.search(r"//\s*([A-Za-z_][A-Za-z_0-9]*)", lines[q])
                if m:
                    slug = m.group(1)
                    break
            lit = re.search(r'==\s*(?:"([^"]+)"|(\d+))', " ".join(lines[i:k + 1]))
            nm_lit = (lit.group(1) or lit.group(2)) if lit else "x"
            blocks.append((nm_lit, i, j, cond, slug, k))
            i = j + 1
            continue
        if lines[i].strip() and not lines[i].lstrip().startswith("//"):
            others.append((i, lines[i].strip()))
        i += 1
    return lines, s, e, ret_i64, blocks, others, pname, params, extra


def main():
    mode, rel, func, var, outfile = sys.argv[1:6]
    path = os.path.join(ROOT, "compiler", rel.replace("/", os.sep))
    lines, s, e, ret_i64, blocks, others, pname, params, extra = analyze(path, func, var)
    prefix = func + "_b"
    print("%s: %s @%d..%d (%d 行) 返回 i64=%s；首参名=%s；分支 %d，非分支语句 %d"
          % (func, rel, s + 1, e + 1, e - s + 1, ret_i64, pname, len(blocks), len(others)))
    if not blocks:
        print("无匹配分支，终止（检查分派变量名）")
        return
    tot = sum(b - a + 1 for _, a, b, _, _, _ in blocks)
    print("  分支合计 %d 行，最大 %d；调度器收敛后约 %d 行"
          % (tot, max(b - a + 1 for _, a, b, _, _, _ in blocks), len(others) + len(blocks) + 3))
    for num, a, b, cond, slug, k in blocks:
        print("    %-24s %4d 行  %s" % ("%s_%s%s" % (prefix, num, ("_" + slug) if slug else ""),
                                       b - a + 1, cond[:40]))
    if mode != "apply":
        return
    pre_lines = lines[s + 1:blocks[0][1]] if blocks else []
    ns = ns_name(lines)
    out = ["type tie<class>",
           "// compiler/%s —— %s 的分支生成器（p.9.21.3 函数级拆解）" % (outfile, func),
           "// ============================================================",
           "// 由 split_dispatch.py 自 %s 的 %s 提取：每个 `%s == N` 分支一个函数，"
           % (rel, func, var),
           "// 调度器只留一行一分支的转发；顶层全局 var 与 import 树仍留原文件。",
           ("namespace %s {" % ns) if ns else ""]
    used = {}
    for num, a, b, cond, slug, k in blocks:
        name = "%s_%s%s" % (prefix, re.sub(r"[^A-Za-z0-9_]", "_", num), ("_" + slug) if slug else "")
        while name in used:
            name += "_x"
        used[name] = True
        body = lines[k + 1:b]
        body_txt = "\n".join(body)
        # 分支体引用的 dispatcher 前导语句（var op = ... / reg 赋值等）随体复制
        # 前导语句整体复制（逐行过滤会切断多行 if 的括号配对，实测踩过）
        pre = pre_lines
        sig = "pub func %s(%s)%s {" % (name, ", ".join("%s: %s" % (n, t) for n, t in params), " -> i64" if ret_i64 else "")
        out.append(sig)
        out.extend(pre)
        out.extend(body)
        out.append("}")
        out.append("")
    if ns:
        out.append("}")
    with io.open(os.path.join(os.path.dirname(path), outfile), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    print("[写出] compiler/%s（函数 %d）" % (outfile, len(blocks)))

    # 重建调度器
    new = [lines[s]]
    i = s + 1
    idx = 0
    while i < e:
        if idx < len(blocks) and i == blocks[idx][1]:
            num, a, b, cond, slug, k = blocks[idx]
            name = "%s_%s%s" % (prefix, re.sub(r"[^A-Za-z0-9_]", "_", num), ("_" + slug) if slug else "")
            call = "%s(%s)" % (name, ", ".join(n for n, _ in params))
            if ret_i64:
                new.append("    if %s { return %s }" % (cond, call))
            else:
                new.append("    if %s {" % cond)
                new.append("        %s" % call)
                new.append("        return")
                new.append("    }")
            i = b + 1
            idx += 1
            continue
        new.append(lines[i])
        i += 1
    new.append("}")
    out2 = lines[:s] + new + lines[e + 1:]
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out2))
    print("[更新] compiler/%s（%d 行，%s %d 行）" % (rel, len(out2), func, len(new)))


main()
