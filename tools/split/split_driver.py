"""driver.tie 拆分抽取器 v2（同 namespace 跨文件范式 + 顶层平铺遗留文件）。

用法：
  python split_drv2.py plan                 # 打印分组计划
  python split_drv2.py apply <group,...>    # 执行抽取

范式（对齐 irgen 系列 + 本轮实测约束）：
  * 拆出文件两种风格：
      - flat：不带 namespace、不带 pub 的顶层函数文件。用于**被同单元其他组件
        裸名依赖**的共享工具（实测 consteval.tie 等 12+ 处裸调 driver 顶层 slice/trim/
        split_lines…）；等语言层 L1 可见性梯度落地后再收敛进 driver ns。
      - ns  ：`namespace driver { pub func ... }`（driver 自有逻辑，无外部裸依赖）。
  * 拆出文件只含函数与注释：不含 import、不含顶层全局 var（全局 var 与 import 树留在主文件）。
  * main 必须留在主文件顶层（放进 ns 会导致链接期缺入口，LNK1561 实测）。
  * ns 文件内的调用保持裸名：实测「ns 内函数可裸名调用同单元顶层函数」，且同 ns 跨文件
    互调同样裸名可用（irgen 先例）；主文件顶层代码调 ns 函数须 `driver.<名>()`（且须 pub）。
  * 抽取只搬函数体与其紧邻上方注释块，绝不触碰 `var` 行（曾因连带删除前一行而丢全局
    var 声明 g_name_mods）。
"""
import io
import os
import re
import sys

# 仓库根：环境变量 TIEC_ROOT 优先，其次当前工作目录（原脚本写死本机绝对路径）
ROOT = os.environ.get("TIEC_ROOT") or os.getcwd()
MAIN = ROOT + r"\compiler\driver.tie"

# name -> (文件, 说明, 函数名列表, 风格 flat|ns)
GROUPS = {
    "util": ("driver/util.tie", "driver 文本/路径工具子模块", "flat", [
        "find_str", "split_char", "base_dir_of", "strip_type_header", "split_lines",
        "has_prefix", "find_char", "slice", "trim", "dir_of", "replace_ext",
        "file_name_of", "role_from_filename", "detect_shared_mode", "has_dll_so_ext",
        "is_linux_target",
    ]),
    "cli": ("driver/cli_args.tie", "driver CLI 参数与头部扫描子模块", "ns", [
        "usage", "parse_opt_level", "parse_args", "normalize_target", "scan_header",
    ]),
    "role": ("driver/role_reg.tie", "driver 角色注册表子模块", "ns", [
        "reg_base", "reg_mod", "role_registry_init_default", "register_role_map",
        "pkg_deps_start", "pkg_deps_end", "pkg_dep_pairs", "dep_roles_path",
        "role_registry_scan_project", "role_registry_boot", "role_registered",
        "is_valid_mod_role", "is_valid_role_param", "is_valid_base_role",
        "role_output", "tsh_dispatch", "parse_role_decl",
    ]),
    "front": ("driver/front_end.tie", "driver 前端调用与诊断输出子模块", "ns", [
        "frontend", "print_warns", "err_span",
    ]),
    "keelcli": ("driver/keelcli.tie", "driver keel 子命令子模块", "ns", [
        "keelcli_is_subcmd", "keelcli_cmd_stub", "keelcli_handle", "keelcli_pkg_handle",
    ]),
    "pipe": ("driver/pipeline.tie", "driver 编译管线（kpass 序列 / 后端驱动）子模块", "ns", [
        "kpass_front", "kpass_irgen", "kpass_tieir", "kpass_trmemit", "kpass_emit",
        "effective_llvm_opt", "effective_tie_opt", "kpass_link", "keel_driver_boot",
        "keel_dispatch", "keel_run_pipeline", "compile_program", "compile_logic",
        "compile_library", "compile_shared", "cleanup",
    ]),
    "cache": ("driver/cache_drv.tie", "driver 依赖感知缓存子模块", "ns", [
        "cache_dir_value", "dep_depset", "dep_file_fp", "dep_sort_strings",
        "dep_cache_key", "dep_manifest_text", "dep_manifest_ok", "cache_try_hit_dep",
        "cache_store_dep", "str_hash", "cache_key_str", "output_artifact_path",
        "cache_enabled",
    ]),
}


def read_main():
    with io.open(MAIN, encoding="utf-8") as fh:
        return fh.read().split("\n")


def func_ranges(lines):
    out = []
    i, n = 0, len(lines)
    while i < n:
        m = re.match(r"^func\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(", lines[i])
        if not m:
            i += 1
            continue
        depth, started, j = 0, False, i
        while j < n:
            depth += lines[j].count("{") - lines[j].count("}")
            if "{" in lines[j]:
                started = True
            if started and depth <= 0:
                break
            j += 1
        out.append((m.group(1), i, j))
        i = j + 1
    return out


def qualifies(text, names):
    if not names:
        return text
    pat = "|".join(sorted(names, key=len, reverse=True))
    call_re = re.compile(r"(?<![\w.])(" + pat + r")\s*\(")
    out = []
    for ln in text.split("\n"):
        st = ln.lstrip()
        if st.startswith("//") or st.startswith("import ") or st.startswith("type tie"):
            out.append(ln)
            continue
        if re.match(r"^(pub )?func ", st):
            out.append(ln)
            continue
        out.append(call_re.sub(lambda m: "driver." + m.group(1) + "(", ln))
    return "\n".join(out)


def plan():
    lines = read_main()
    by_name = {nm: (a, b) for nm, a, b in func_ranges(lines)}
    moved = set()
    total = 0
    for key, (path, desc, style, names) in GROUPS.items():
        miss = [x for x in names if x not in by_name]
        ln = sum(by_name[x][1] - by_name[x][0] + 1 for x in names if x in by_name)
        total += ln
        moved.update(names)
        print("%-9s %-30s %-4s 函数 %2d 行 %5d 缺失=%s" % (key, path, style, len(names), ln, miss or "-"))
    print("拆出合计=%d；main 保留顶层函数=%s" % (
        total, [nm for nm, a, b in func_ranges(lines) if nm not in moved]))


def apply(groups):
    lines = read_main()
    rs = func_ranges(lines)
    by_name = {nm: (a, b) for nm, a, b in rs}
    moved_all = set()
    ns_moved = set()
    for g in groups:
        moved_all.update(GROUPS[g][3])
        if GROUPS[g][2] == "ns":
            ns_moved.update(GROUPS[g][3])
    unknown = [x for x in moved_all if x not in by_name]
    assert not unknown, "未找到函数: %s" % unknown

    for g in groups:
        path, desc, style, names = GROUPS[g]
        body = []
        for nm in names:
            a, b = by_name[nm]
            k = a - 1
            while k >= 0 and lines[k].lstrip().startswith("//"):
                k -= 1
            body.extend(lines[k + 1:b + 1])
            body.append("")
        head = [
            "type tie<class>",
            "// compiler/%s —— %s" % (path, desc),
            "// ============================================================",
            "// 从 driver.tie 拆出（p.9.21 方法库化：driver 编排薄壳）。",
            "// 拆分范式：同编译单元跨文件（文本内联）——本文件只含函数与注释，",
            "// 顶层全局 var 与 import 树均留在 driver.tie 主文件，避免重复定义。",
        ]
        if style == "ns":
            head += [
                "// 风格 ns：函数在 `namespace driver` 内，一律 pub（driver 库 API 面）；",
                "// 主文件顶层 main() 以 driver.<名>() 调用。",
                "namespace driver {",
            ]
        else:
            head += [
                "// 风格 flat：顶层平铺函数。本组工具被同单元其他组件裸名依赖（实测",
                "// consteval.tie 等 12+ 处裸调 slice/trim/split_lines…），收进 ns 会切断",
                "// 这些调用；待语言层 L1 可见性梯度落地后再收敛进 driver ns。",
            ]
        lines_out = head + body + (["}"] if style == "ns" else [])
        target = os.path.join(ROOT, "compiler", path.replace("/", "\\"))
        with io.open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines_out))
        print("[写出] compiler/%s（风格 %s，函数 %d 个）" % (path, style, len(names)))

    drop = set()
    for nm in moved_all:
        a, b = by_name[nm]
        k = a - 1
        while k >= 0 and lines[k].lstrip().startswith("//"):
            k -= 1
        for idx in range(k + 1, b + 2):
            drop.add(idx)
    kept = [ln for idx, ln in enumerate(lines) if idx not in drop]
    imp = [i for i, ln in enumerate(kept) if ln.startswith("import ")]
    news = ['import "./%s"' % GROUPS[g][0] for g in groups]
    kept = kept[:imp[-1] + 1] + news + kept[imp[-1] + 1:]

    text = qualifies("\n".join(kept), ns_moved)
    with io.open(MAIN, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("[更新] compiler/driver.tie（%d 行，限定名仅对 ns 组）" % len(text.split("\n")))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if mode == "plan":
        plan()
    else:
        apply(sys.argv[2].split(","))
