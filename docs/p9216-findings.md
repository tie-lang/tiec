# p.9.21.6 模块级增量编译 —— 落地记录与发现 / p.9.21.6 Findings

> 2026-09-23。p921-prompt §1（模块边界 → 按模块缓存 → 提速数据）执行记录、
> 自检发现的缺陷与后续立项。执行者无需读本轮对话。
> EN: Execution record for p.9.21.6 plus defects surfaced by the new self-checks.

## 1. 已落地 / Landed

| 提交 | 内容 |
| --- | --- |
| 42c85c6 | 模块边界显式化：`g_file_base`（每文件 AST 节点基址）+ `sg_mod`/`gb_mod`/`st_mod` 来源模块列 + `file_id_of_node` 等访问器（8 文件，纯增量元数据） |
| 2e0b91c | 模块级 tieir 片段缓存：`middle/tieir_slice.tie`（write_mod_slice，重映射表版）+ driver 归属注入/键管理 + 盐 v1→v2（p.9.19.8 遗留）+ tieir_test 片段 roundtrip 自检 |
| bd876d1 | 片段缓存默认关（`TIEC_MODCACHE=1`）：全量池片段在大单元（driver ~200 模块）写放大 27s→68s；池过滤（层 II 收口）后默认开 |
| （本轮）| `middle/passes_test.tie`（passes 库独立自检）+ `lex_test.tie` token 基线重录 + `scripts/verify-modcache.tsh.tie` 验收脚本 |

不动点：c54f1610 → 6313365a（步 1）→ d7e2fd54（步 2）→ **2e238f60**（门控后现值）。
回归：每步后 157 PASS / 8 FAIL / 2 SKIP 与基线一致。

## 2. 验收数据（操作台实测）/ Acceptance data

* 模块片段缓存四步验收（tests/_modcache_probe 菱形导入工程）：
  冷启 +4 片段 → 原样重编 +0（全命中）→ 改叶子恰 +1（其余 3 模块命中）→
  带缓存产物 == --no-cache 产物（SHA256 逐字节一致）。
* 提速数据（driver 自举基准，-l2 -t0）：全量 26.8s；单元依赖缓存命中
  15.1s（1.8×，命中成本 = ~200 依赖文件指纹复核对账）；语言语料 30 文件
  平均 1.24s/文件。模块级**跳过编译**（片段组装消费）为层 II 收口项，
  当前片段为证据级（命中判定/产物形态/自检），不改变编译耗时。
* passes 库自检（middle/passes_test.tie）：两常量相加经 run(1) 折叠为
  const_i 5 + DCE 收缩 4→2 指令；t0 零改动；t1 幂等；pipeline_ver 稳定。

## 3. 发现的缺陷（已立项）/ Defects surfaced

### D1 tieir 反序列化不支持真实多函数单元（高优，立 p.9.21.7）
`tieir.read` 的 fpo 校验假设「参数段在 ops 段内连续」，而 irgen 边建函数边建体，
真实布局是每函数 [参数][指令操作数] 交错（fn1.params_off=15 ≠ 累计参数 2）。
**自产的 --tieir-out 单元无法通过自身 tieir.read**（复现：`_tiec_verify/rr_probe.tie`
READ_FAIL: 函数参数段偏移不一致(函数 1)）。单函数自检掩盖了它。
修法 = 反序列化值重映射（与 tieir_slice.write_mod_slice 的重映射对偶）。

### D2 trm loader 版本闸滞后（已在 trm 仓修复）
trm `core/frontend/loader.tie` 只接受格式 v1，拒收 tiec p.9.20 起的 v2
（模块头多 t 档 + pass 版本两字段）。已改：v1/v2 双接受，v2 读入并记录
新字段（l_format_ver/l_tie_opt/l_pass_ver）。注：trm loader 吃文本字节 CSV
（历史 byte_read 崩溃 workaround），二进制 .tieir 需经 tieir2csv 桥
（_tiec_verify/tieir2csv.tie）；D1 解开后建议 trm 改直读二进制。

### D3 词法诊断列号为字节列，golden 期望码点列（先前已存在）
lex_test 负例「码点列号」：期望 @1:13，实际 @1:9（UTF-8 多字节前缀差 4）。
诊断列号应对齐码点。独立于本次基线重录，另行修复。

### D4 bootstrap-fp.tsh.tie 参数处理（tsh REPL v1 语义）
脚本内 `out = arg_at(0)` 在恰好 1 个脚本参数时静默不生效（探针证明
arg_at/is_empty/分支判定均正常），2 参数（out + fresh）正常；[4/4] 的哈希
打印始终读默认目录。已用「双参数调用 + 产物直哈希复核」绕开；
tsh 侧根因（exec/list_dir/file_read/file_exists 的进程内缓存与异步返回）
见 §4，修 tsh 后回改脚本。

## 4. tsh REPL v1 语义实测备忘（写脚本者必读）
* exec_code **异步返回**：子进程可能未写完文件——读产物前必须 sleep/轮询。
* list_dir 对同一路径**进程内缓存**：同路径重复列出拿陈旧列表（换路径拼写可绕）。
* file_read/file_exists 同样有缓存语义（首次观测被记住）。
* exec_output 对裸内部命令（`set X=1&& …`）返回空，须显式 `cmd /c` 包装；
  管道/重定向组合不稳（bootstrap-fp 头注既有告诫）。
* `bootstrap-fp.tsh.tie` 单参数调用 out 静默回退默认目录——**永远双参数调用**，
  并对产物直接 certutil 复核哈希。

## 5. 后续排序 / Next
1. p.9.21.7：tieir 反序列化布局忠实重建（D1，含值重映射 + 多函数 roundtrip 自检）。
2. 片段池过滤（写放大消除）→ 模块缓存默认开。
3. 片段组装消费（改叶子只重编该模块的前端/irgen 路径）→ 层 II 收口。
4. D3 词法码点列号；trm loader 直读二进制（D2 收尾）。
5. tsh REPL v1 语义修复（D4/§4）后回改 bootstrap-fp 参数处理。
