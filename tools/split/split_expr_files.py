"""irgen_expr.tie 的文件级拆解（p.9.21.2/3）：把 129 个 namespace 内嵌函数与
三个顶层函数按域搬到独立文件，使 irgen_expr.tie 降到 800 行以内。

用法：
  python split_expr_files.py plan
  python split_expr_files.py apply
"""
import io
import os
import re
import sys

# 仓库根：环境变量 TIEC_ROOT 优先，其次当前工作目录（原脚本写死本机绝对路径）
ROOT = os.environ.get("TIEC_ROOT") or os.getcwd()
SRC = ROOT + r"\compiler\backend\irgen_expr.tie"
IMPORTER = ROOT + r"\compiler\backend\irgen.tie"

DESC = {
    "irgen_strutil.tie": "生成器 L3：字符串/字节查找辅助（starts_with/bfind/bytes_sub/cstr_len）",
    "irgen_huff.tie": "生成器 L3：解压 Huffman 码表构建与解码",
    "irgen_conv.tie": "生成器 L3：数值/字符串转换辅助（parse_float/parse_dec/parse_octal/clen/…）",
    "irgen_bits.tie": "生成器 L3：字节/位/宽字符原语辅助（byte_*、bit_*、w16_*、wide16、cp_utf8、le_*）",
    "irgen_proc.tie": "生成器 L3：进程/参数/环境辅助（exec_output_*、arg_*、cwd、set_env、sh_op）",
    "irgen_stdio.tie": "生成器 L3：标准输入输出辅助（stdin_read、stdout_write_*、read_line）",
    "irgen_msgrt.tie": "生成器 L3：消息系统与随机数运行时辅助（msg_*、rng_reg、rand_range）",
    "irgen_net.tie": "生成器 L3：TCP/解析辅助（wsa_init、net_resolve、net_tcp_*）",
    "irgen_netudp.tie": "生成器 L3：UDP 辅助（net_udp_*）",
    "irgen_fs.tie": "生成器 L3：文件系统辅助（open/stat/read/write/exists/size/delete/copy/move）",
    "irgen_dir.tie": "生成器 L3：目录遍历辅助（mkdir_all/remove_dir_all/copy_dir/list_dir/blob_push/walk_dir）",
    "irgen_http.tie": "生成器 L3：HTTP 客户端辅助（url_parse、http_fetch/get/get_file、write_region）",
    "irgen_inflate.tie": "生成器 L3：解压内核（字节/位读取、huffman、inflate_raw）",
    "irgen_archive.tie": "生成器 L3：归档格式辅助（gzip 头、tar 解包、untar_gz、zip EOCD、unzip）",
    "irgen_dispatch.tie": "生成器 L3：内置表达式调度器（builtin_expr，p.9.21.2 两步制①产物）",
    "irgen_switch.tie": "生成器 L3：switch 表达式生成（tig_switch_expr）",
}

BT = ["tig_bt_mode2", "tig_bt_fail", "tig_bt_fseek", "tig_bt_fread", "tig_bt_fwrite",
      "tig_bt_fclose"]
STRUTIL = ["tig_str_starts_with", "tig_tolower_b", "tig_bfind", "tig_bytes_sub", "tig_cstr_len"]
HUFF = ["tig_huff_build", "tig_huff_decode"]
FS_A = ["tig_is_linux", "tig_posix_open3", "tig_posix_stat_mode", "tig_posix_stat_size",
        "tig_posix_copy_file", "tig_mkdir_utf8", "tig_create_file_w", "tig_file_attr_w",
        "tig_mkdir_w", "tig_find_first_w", "tig_find_next_w", "tig_find_close",
        "tig_is_dotname", "tig_read_file", "tig_write_file", "tig_attr_invalid",
        "tig_exists_inline", "tig_is_dir_inline", "tig_is_file_inline", "tig_size_inline",
        "tig_delete_inline", "tig_copy_file", "tig_move_file", "tig_posix_list_names"]
FS_B = ["tig_mkdir_all", "tig_remove_dir_all", "tig_copy_dir", "tig_list_dir",
        "tig_walk_dir"]
CONV = ["tig_f64_to_str", "tig_parse_float", "tig_parse_dec", "tig_parse_octal",
        "tig_parse_clen", "tig_not_i1", "tig_trunc_i32", "tig_p2i", "sio_trunc_i32"]
BITS = ["tig_byte_read", "tig_byte_write", "tig_bit_read", "tig_bit_write",
        "tig_byte_concat", "tig_w16_append", "tig_w16_append_cp", "tig_wide16",
        "tig_cp_utf8_append", "tig_from_wide16", "tig_bytes_to_tie", "tig_le_u16",
        "tig_le_u32", "tig_wide16_dbl", "tig_null_ptr", "tig_wildpath", "tig_join_path",
        "tig_fill_table", "tig_slot64", "tig_win_ok"]
PROC = ["tig_exec_output_posix", "tig_exec_output_inline", "tig_arg_count", "tig_arg_string",
        "tig_cwd", "tig_set_env", "tig_print_err", "tig_sh_op"]
STDIO = ["tig_stdin_read", "tig_stdout_write_str", "tig_stdout_write_bytes", "tig_read_line"]
MSGRT = ["tig_msg_reg_globals", "tig_msg_gload", "tig_msg_gstore", "tig_msg_ensure",
         "tig_msg_str_eq", "tig_msg_register", "tig_msg_find", "tig_rng_reg", "tig_rand_range"]
NET = ["tig_wsa_init", "tig_wsa_addr", "tig_net_socket", "tig_net_resolve",
       "tig_net_tcp_listen", "tig_net_tcp_accept", "tig_net_tcp_connect", "tig_net_tcp_send",
       "tig_net_tcp_recv", "tig_net_tcp_send_bytes", "tig_net_tcp_recv_bytes", "tig_net_close"]
NETUDP = ["tig_net_udp_bind", "tig_net_udp_send", "tig_net_udp_recv",
          "tig_net_udp_send_bytes", "tig_net_udp_recv_bytes"]
HTTP = ["tig_url_parse", "tig_http_fetch", "tig_http_get", "tig_http_get_file", "tig_write_region"]
INFLATE = ["tig_sb_len", "tig_sb_data", "tig_ib_read1", "tig_ib_readn", "tig_ib_read8",
           "tig_inflate_raw"]
ARCHIVE = ["tig_join_slash", "tig_dirname", "tig_gzip_skip_header", "tig_tar_extract",
           "tig_untar_gz", "tig_zip_find_eocd", "tig_unzip"]


def mapping():
    m = {}
    for names, fn in ((STRUTIL, "irgen_strutil.tie"), (HUFF, "irgen_huff.tie"),
                      (BT, "irgen_fs.tie"),
                      (CONV, "irgen_conv.tie"), (BITS, "irgen_bits.tie"),
                      (PROC, "irgen_proc.tie"), (STDIO, "irgen_stdio.tie"),
                      (MSGRT, "irgen_msgrt.tie"), (NET, "irgen_net.tie"),
                      (NETUDP, "irgen_netudp.tie"), (FS_A, "irgen_fs.tie"),
                      (FS_B, "irgen_dir.tie"), (HTTP, "irgen_http.tie"),
                      (INFLATE, "irgen_inflate.tie"), (ARCHIVE, "irgen_archive.tie")):
        for n in names:
            m[n] = fn
    m["tig_blob_push"] = "irgen_fs.tie"
    m["tig_pad512"] = "irgen_archive.tie"
    m["tig_switch_expr"] = "irgen_switch.tie"
    m["builtin_expr"] = "irgen_dispatch.tie"
    return m


def read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read().split("\n")


def brace_end(lines, i):
    d = 0
    j = i
    while j < len(lines):
        d += lines[j].count("{") - lines[j].count("}")
        if j > i and d == 0:
            return j
        j += 1
    return len(lines) - 1


def items(lines):
    """返回 [(name, start, end)]，含 0 缩进与 4 缩进的函数定义。"""
    out = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)func ([A-Za-z_][A-Za-z_0-9]*)\s*\(", lines[i])
        if m:
            j = brace_end(lines, i)
            out.append((m.group(2), i, j))
            i = j + 1
            continue
        i += 1
    return out


def extend_up(lines, a, floor):
    k = a - 1
    while k > floor and lines[k].lstrip().startswith("//"):
        k -= 1
    return k + 1


def plan():
    lines = read(SRC)
    mm = mapping()
    its = items(lines)
    agg = {}
    unknown = []
    for nm, a, b in its:
        fn = mm.get(nm)
        if not fn:
            unknown.append(nm)
            continue
        agg.setdefault(fn, []).append(b - a + 1)
    for fn in sorted(agg):
        print("%-24s 函数 %3d 行之和 %5d（加头部约 %d）" % (fn, len(agg[fn]), sum(agg[fn]),
                                                        sum(agg[fn]) + 4 * len(agg[fn]) + 9))
    print("留在 irgen_expr.tie 的函数:", unknown)


def apply():
    lines = read(SRC)
    mm = mapping()
    its = items(lines)
    groups = {}
    for nm, a, b in its:
        fn = mm.get(nm)
        if not fn:
            continue
        s = extend_up(lines, a, 0)
        groups.setdefault(fn, []).append((nm, s, b))
    for fn, arr in groups.items():
        parts = []
        for nm, s, b in arr:
            body = [(l[4:] if l.startswith("    ") else l) for l in lines[s:b + 1]]
            parts.append("\n".join(body) + "\n")
        head = [
            "type tie<class>",
            "// compiler/backend/%s —— %s" % (fn, DESC.get(fn, "")),
            "// ============================================================",
            "// 自 irgen_expr.tie 按域拆出（p.9.21.2/3：单文件 ≤800 行）。",
            "// 范式：同 namespace 跨文件（文本内联）——只含函数与注释，",
            "// 顶层全局 var 与 import 树留在 irgen.tie 主文件。",
            "namespace irgen {",
        ]
        with io.open(os.path.join(ROOT, "compiler", "backend", fn), "w",
                     encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(head) + "\n" + "".join(parts) + "}")
        print("[写出] compiler/backend/%s（函数 %d 个）" % (fn, len(arr)))

    drop = set()
    for fn, arr in groups.items():
        for nm, s, b in arr:
            for k in range(s, b + 1):
                drop.add(k)
    kept = [ln for i, ln in enumerate(lines) if i not in drop]
    with io.open(SRC, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(kept))
    print("[更新] compiler/backend/irgen_expr.tie（%d 行）" % len(kept))

    il = read(IMPORTER)
    ins = [i for i, ln in enumerate(il) if ln.startswith("import ")]
    have = "\n".join(il)
    news = ['import "./%s"' % f for f in sorted(groups) if ('import "./%s"' % f) not in have]
    if news:
        il = il[:ins[-1] + 1] + news + il[ins[-1] + 1:]
        with io.open(IMPORTER, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(il))
        print("[更新] compiler/backend/irgen.tie（补 %d 条 import）" % len(news))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "plan"
    plan() if mode == "plan" else apply()
