"""irgen_expr.tie 的 builtin_expr 两步制①：内置分支提为 bi_* 函数（v2，区域化提取）。

用法：
  python split_bi2.py plan
  python split_bi2.py apply

要点（v2 相对 v1 的两处实测修正）：
  * else-if 链块（`} else if nm == ...`）必须**整块**搬（含起始 if 与最终闭合 }），
    否则函数体少一个 } 会把后续函数吞进体内；
  * 链块常与相邻语句共享局部变量（如 as_* 链前的 `var as_dst` 与链后的
    `if as_dst >= 0`）——按**区域**提取：向上吞并紧邻的 `var`/注释行，向下吞并
    直到下一个 `    if nm == "` 块起点；若被吞并的变量在区域外仍被引用，则放弃
    该链的提取（留在 builtin_expr 内，避免语义变化）。
"""
import io
import os
import re
import sys

# 仓库根：环境变量 TIEC_ROOT 优先，其次当前工作目录（原脚本写死本机绝对路径）
ROOT = os.environ.get("TIEC_ROOT") or os.getcwd()
SRC = ROOT + r"\compiler\backend\irgen_expr.tie"
MAIN_IMPORTER = ROOT + r"\compiler\backend\irgen.tie"

SECTION_FILE = {
    "S1.2": "irgen_bi_mem.tie",
    "S1.3 as": "irgen_bi_num.tie",
    "S1.3 checked": "irgen_bi_num.tie",
    "S2.1": "irgen_bi_str.tie",
    "网络": "irgen_bi_net.tie",
    "动态加载": "irgen_bi_dyn.tie",
    "M4/M6": "irgen_bi_sys.tie",
    "p.6.4.7": "irgen_bi_msg.tie",
    "trm-lite": "irgen_bi_trm.tie",
    "channel": "irgen_bi_trm.tie",
    "p.6.7.12": "irgen_bi_trm.tie",
    "WaitGroup": "irgen_bi_trm.tie",
}
FILE_DESC = {
    "irgen_bi_mem.tie": "内置生成器：unsafe 指针/内存（S1.2）",
    "irgen_bi_num.tie": "内置生成器：显式数值转换 as_* 与 checked_* 溢出检测（S1.3）",
    "irgen_bi_str.tie": "内置生成器：字符串 {ptr,len} 原语（S2.1）",
    "irgen_bi_net.tie": "内置生成器：网络原语（std/net）",
    "irgen_bi_dyn.tie": "内置生成器：动态加载原语（winsqlite3.dll C ABI 桥）",
    "irgen_bi_sys.tie": "内置生成器：系统能力（M4/M6）",
    "irgen_bi_msg.tie": "内置生成器：消息系统原语（p.6.4.7）",
    "irgen_bi_trm.tie": "内置生成器：trm-lite 执行体 / channel / ch_select / WaitGroup",
}


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read().split("\n")


def line_delta(ln):
    """字符串/注释感知的花括号净增量。"""
    d = 0
    i = 0
    n = len(ln)
    in_str = False
    while i < n:
        c = ln[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == "/" and i + 1 < n and ln[i + 1] == "/":
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
        chain = lines[j].lstrip().startswith("} else")
        if d <= 0 and not chain and j > start:
            return j
        j += 1
    return limit


def find_func(lines, name):
    for i, ln in enumerate(lines):
        if re.match(r"^func %s\(" % re.escape(name), ln):
            return i, block_end(lines, i, len(lines))
    raise SystemExit("未找到函数 %s" % name)


def blocks(lines, start, end):
    """返回 [(name, a, b, is_chain, sect, ext_start, ext_end, inline_only)]"""
    out = []
    sect = "未分段"
    i = start + 1
    while i < end:
        ln = lines[i]
        m = re.match(r"^    // -{3,}\s*(.+?)\s*-{3,}\s*$", ln)
        if m:
            sect = m.group(1).strip()
            i += 1
            continue
        m = re.match(r'^    if nm == "([^"]+)" \{\s*$', ln)
        if not m:
            i += 1
            continue
        j = block_end(lines, i, end + 1)
        is_chain = any(lines[k].lstrip().startswith("} else") for k in range(i, j + 1))
        es, ee, inline = i, j, False
        if is_chain:
            k = i - 1
            while k > start and (lines[k].lstrip().startswith("var ") or
                                 lines[k].lstrip().startswith("//")):
                es = k
                k -= 1
            jj = j + 1
            while jj < end and not re.match(r'^    if nm == "', lines[jj]):
                ee = jj
                jj += 1
            hoisted = [re.match(r"\s*var ([A-Za-z_][A-Za-z_0-9]*)", lines[p]).group(1)
                       for p in range(es, i)
                       if re.match(r"\s*var ([A-Za-z_][A-Za-z_0-9]*)", lines[p])]
            outside = "\n".join(lines[start:es] + lines[ee + 1:end + 1])
            for nmv in hoisted:
                if re.search(r"(?<![\w.])%s(?![\w])" % re.escape(nmv), outside):
                    inline = True
        out.append((m.group(1), i, j, is_chain, sect, es, ee, inline))
        i = j + 1
    return out


def sanitize(nm):
    s = re.sub(r"[^A-Za-z0-9_]", "_", nm)
    return ("_" + s) if re.match(r"^[0-9]", s) else s


def target_file(sect):
    for key, fn in SECTION_FILE.items():
        if sect.startswith(key):
            return fn
    return "irgen_bi_misc.tie"


def plan():
    lines = read(SRC)
    s, e = find_func(lines, "builtin_expr")
    bs = blocks(lines, s, e)
    print("builtin_expr @%d..%d（%d 行），块 %d（其中就地保留 %d）"
          % (s + 1, e + 1, e - s + 1, len(bs), sum(1 for b in bs if b[7])))
    agg = {}
    for nm, a, b, chain, sect, es, ee, inline in bs:
        if inline:
            print("  就地保留（共享变量越界引用）: %s @%d..%d" % (nm, es + 1, ee + 1))
            continue
        agg.setdefault(target_file(sect), []).append(ee - es + 1)
    for fn in sorted(agg):
        print("  %-22s 块 %3d 行之和 %5d 最大 %4d" % (fn, len(agg[fn]), sum(agg[fn]), max(agg[fn])))
    est = sum(1 for b in bs if b[7]) * 40 + (len(bs) - sum(1 for b in bs if b[7]))
    print("调度链 + 就地保留 ≈ %d 行" % (est + 45))


def apply():
    lines = read(SRC)
    s, e = find_func(lines, "builtin_expr")
    bs = blocks(lines, s, e)
    by_file = {}
    for nm, a, b, chain, sect, es, ee, inline in bs:
        if inline:
            continue
        by_file.setdefault(target_file(sect), []).append((nm, a, b, chain, sect, es, ee))
    for fn, items in by_file.items():
        parts = []
        for nm, a, b, chain, sect, es, ee in items:
            body_txt = "\n".join(lines[es:ee + 1])
            need_nm = chain or re.search(r"(?<![\w.])nm(?![\w])", body_txt) is not None
            sig = ("pub func bi_%s(nm: string, id: i64) -> i64 {" % sanitize(nm)) if need_nm else \
                  ("pub func bi_%s(id: i64) -> i64 {" % sanitize(nm))
            head = ["// " + sect,
                    "// 内置 `%s`（p.9.21.2 两步制①：自 builtin_expr 提取）" % nm,
                    sig]
            body = [(l[4:] if l.startswith("    ") else l) for l in lines[es:ee + 1]]
            parts.append("\n".join(head + body + ["}", ""]))
        head = [
            "type tie<class>",
            "// compiler/backend/%s —— %s" % (fn, FILE_DESC.get(fn, "内置生成器")),
            "// ============================================================",
            "// 自 irgen_expr.tie 的 builtin_expr 拆出（p.9.21.2 两步制①）。",
            "// 范式：同 namespace 跨文件（文本内联）——只含函数与注释，",
            "// 顶层全局 var 与 import 树留在 irgen.tie 主文件。",
            "namespace irgen {",
        ]
        with io.open(os.path.join(ROOT, "compiler", "backend", fn), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(head + parts + ["}"]))
        print("[写出] compiler/backend/%s（块 %d 个）" % (fn, len(items)))

    # 重写 builtin_expr
    drops = []
    calls = {}
    for nm, a, b, chain, sect, es, ee, inline in bs:
        calls[a] = (nm, chain, inline, es, ee, need_nm)
        drops.append((max(es, a - 1 if not chain else es), ee))
    newb = ["func builtin_expr(nm: string, id: i64) -> i64 {"]
    last_sect = None
    i = s + 1
    while i < e:
        if i in calls:
            nm, chain, inline, es, ee, need_nm = calls[i]
            sect = next(x[4] for x in bs if x[1] == i)
            if sect != last_sect:
                newb.append("    // ---------- %s ----------" % sect)
                last_sect = sect
            if inline:
                newb.extend(lines[es:ee + 1])
            else:
                call = ("bi_%s(nm, id)" % sanitize(nm)) if need_nm else ("bi_%s(id)" % sanitize(nm))
                newb.append('    if nm == "%s" { return %s }' % (nm, call))
            i = ee + 1
            continue
        newb.append(lines[i])
        i += 1
    newb.append("}")
    out = lines[:s] + newb + lines[e + 1:]
    with io.open(SRC, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    print("[更新] compiler/backend/irgen_expr.tie（%d 行 → builtin_expr %d 行）"
          % (len(out), len(newb)))

    il = read(MAIN_IMPORTER)
    ins = [i for i, ln in enumerate(il) if ln.startswith("import ")]
    have = "\n".join(il)
    news = ['import "./%s"' % fn for fn in sorted(by_file) if ('import "./%s"' % fn) not in have]
    if news:
        il = il[:ins[-1] + 1] + news + il[ins[-1] + 1:]
        with io.open(MAIN_IMPORTER, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(il))
        print("[更新] compiler/backend/irgen.tie（补 %d 条 import）" % len(news))


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "plan"
    plan() if m == "plan" else apply()
