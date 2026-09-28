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

## 6. D1-D4 解决记录（同日闭环）/ Resolutions

| 缺陷 | 状态 | 落点 |
| --- | --- | --- |
| D1 tieir 反序列化布局 | ✅ 已修 | tiec 3b07272：deserialize 值空间重映射（原交错序 → 重建参数前缀序），结果连续性 + 函数边界 fpo 连续性双校验；真实 4 函数单元 roundtrip READ_OK；tieir_test 多函数交错 roundtrip 用例 |
| D2 trm loader | ✅ 已修 | trm 6c70b75（v2 版本闸）+ f6b0e20（值空间重映射 + 布局自动探测 + byte_read 直读二进制 .tir + interp alloca/load/store 原语）；run_tiec（真实 .tir）与 run2（gen2 文本遗留）双路全绿 |
| D3 词法列号 golden | ✅ 已修（golden 过时，非列号缺陷） | tiec 3b07272：'@' 已是合法注解符（p.9.11.12）、非 ASCII 一律标识符材料（is_alpha c>127）——负例改用 '~'（符号表缺席），token 基线重录，lex_test 全绿 |
| D4 bootstrap-fp 参数 | ✅ 已加固 | tiec 3b07272：resolve_out() 函数返回式取参（env TIEC_FP_OUT > 参数 > 默认）+ 每使用点现调（tsh 变量赋值不稳定，同轮运行不同语句见到不同值）+ 哨兵写读响亮失败；1 参数调用实测正确建编并打印与产物直核一致的哈希 |

扩展名变更：tieir 产物统一 **.tir**（格式名 tieir 不变；`--tieir-out` 旗标不变）。

不动点：2e238f60 → **7b7d8886**（D1/D3/改名后重录）；回归 157/8/2 每步一致。

解释器/tshell 性能优化：本轮裁定不引入——tsh REPL v1 的语义缺陷（§4）是
一切脚本层测量的前置干扰源，先修语义再加优化；trm interp 的性能调优待其
指令覆盖（br/call 等）补齐后有真实工作负载再测。

## 7. p.9.21.8 片段池过滤 + 模块缓存默认开（2026-09-24）

落点：tiec 5e93660（tieir_slice 池过滤 + tieir_ser 池重映射 + 门控摘除 +
tieir_test 扩展 + 升格）。不动点 7b7d8886 → **25b9bba9**；回归 157/8/2 一致。

* **池引用权威清单**（write_mod_slice 收集 + deserialize 重映射共用）：
  函数名/块名；符号表/导出选中行 name+sig；操作数 kind 3（OK_GLOBAL）；
  kind 0 池载荷**操作数①** = const_str(62)/const_f(51)/call(35)/
  extern_call(36)/call_vararg(41)——与 llvmgen collect_strings/
  collect_externs 消费清单对齐。prompt 原文「const_str 的 kind=2」系笔误
  （实际 kind=0 + opcode 判定）；func_ret/param_ty 是 types.named 小整数
  类型 id（**不是**池 id），不参与池重映射。
* **潜伏缺陷顺手修复**：原 write_mod_slice 对 kind 0 一律做 SSA 值平移，
  池载荷操作数①会被错平移（含字符串字面量的模块片段写入报越界/错位）。
* **deserialize 增强**：池重建时构建「文件 id → 进程 id」映射
  （pool_remap_id），段 4/5/6 池引用统一转换；全量池主单元恒等（D1
  roundtrip 零影响）。压缩池片段的 read/deserialize 从此语义正确。
* **确定性口径修正（重要）**：exe 产物**逐次编译均不同**（同 -o、同源、
  --no-cache 重跑哈希变；旧编译器 7b7d8886 同款复现）——链接器层既有非
  确定性，与模块缓存/本次改动无关。模块缓存确定性验收在 **.tir 产物层**
  做：缓存开 vs --no-cache 逐字节一致 ✓。verify-modcache.tsh.tie 的
  exe 哈希对比步须按此口径修正（本轮手动四步为准）。
* **验收数据**（同机同时段，driver 自举基准 -l2 -t0）：
  | 场景 | 旧版 7b7d8886 | 新版 25b9bba9 |
  | --- | --- | --- |
  | --no-cache 全量 | 30.5s | 30.9s（持平；首跑 36.8s 为磁盘噪声） |
  | 全冷 HOME + 模块缓存开 | 72.9s（TIEC_MODCACHE=1） | 44.4s（默认开） |
  | 片段写增量 | ≈+42.4s | ≈+13.5s（-68%） |
  模块缓存四步：冷启 +4 / 重编 +0 / 叶子改动恰 +1 / .tir SHA 一致。
  verify-modcache.tsh.tie 脚本本身仍受 tsh list_dir/哈希缺陷干扰（其
  头注已自声明「仅作参考」），本轮以手动四步为准。
* **新登记（归 p.9.3.9）**：bootstrap-fp.tsh.tie [4/4] 打印哈希又现陈旧
  值（本轮打印 7b7d8886 旧值，而产物直核 n1=n2=n3=25b9bba9）——tsh
  exec_output 异步/缓存语义缺陷复现；**产物直哈希复核是唯一权威**。

## 8. p.9.21.9 片段组装消费 —— 勘察与口径裁定（2026-09-24）

实现前勘察（tig_ast 函数创建序 + 池序恢复性），结论如下。

### 8.1 装配序可复现（AST 驱动方案可行）
irgen.tig_ast 的函数创建序 = ①合成函数（actor thunk/dispatch，急切生成）
→ ②g_extra_tops 序遍历（FnDef→tig_fn_def；Namespace→tig_ns 递归）→
③尾部合成（--shared 时 rt_init）。合成函数经 mod_attribution_fill 归属
模块 0（主文件片段）；用户函数可经 g_extra_tops（AST 仍在，语义层已跑）
逐函数取名 → file_id_of_node 定位所属片段 → 片段内函数按原序子集提取。
**装配序（全局函数序）可由「主片段合成头部 + g_extra_tops 序 + 主片段
尾部合成」精确复现**，无需片段携带额外序信息。

### 8.2 池段字节一致不可达（口径必须修正）⚠ 需拍板
全量路径 .tir 的池段 = interner 全量 = [前端串（语义层 intern，两路径
相同）] + [IR 串按 irgen 实际 intern 顺序]。irgen 按 g_extra_tops 交错
处理各模块函数体，IR 串（块名/字面量/全局名/extern 符号）的 intern 序是
**函数粒度交错序**；而片段池（p.9.21.8 压缩版）只有「模块内 intern 序」，
**无函数级归属信息**——交错序无法从片段恢复。且 --tieir-out 时点前端串
与 IR 串已混排。结论：**装配路径与全量路径的 .tir 池段必然不同**（池 id
本为进程内句柄，池段差异不影响任何消费者的语义）。

**建议口径**（类比 §7 的 .tir 产物层口径修正）：硬门禁从「全文件逐字节
一致」修订为——
1. 段 4（符号）/段 5（IR 主体）/段 6（导出）/段 7（span）逐字节一致
   （SHA256 分段对比）；
2. 池段串**集合相等**（无缺失/无多余，允许 id 排列差异）；
3. 语义层结构断言（函数/块/指令/值计数与操作数语义）。
此口径下装配正确性的保证强度与全字节一致等价（池段不承载语义）。

### 8.3 实现骨架（下轮落地）
- middle/tieir_asm.tie：asm_from_slices(paths, n)——逐片段 bytes.read →
  自解析段 3-7（不经 tieir.deserialize，避免 ir.new_module 复位）→
  池重映射（片段 id → str_pool 全局 id）→ 函数按 §8.1 序重建 → 值空间
  「参数前缀 cum_params + 结果段 P_total+result_cum」分配 → ops_off/
  params_off 自然偏移 → span 按全局指令位写。
- driver 挂点：kpass_irgen 入口判「n 模块片段键全命中」→ 跳 irgen.tig_ast
  + passes.run（片段已含 pass 结果，键含 t 档），走装配；否则全量路径不变
  （mod_cache_update 照写缺片段）。TIEC_INC=1 打印 MODASM h/n assembled。
- 跨片段常量折叠风险预案照 ROAD：片段头依赖段记被折叠常量来源模块、装配
  时判脏（允许过度失效）。

### 8.4 补充勘察（同日）：装配必须 g_extra_tops 驱动，片段拼接序不成立
g_extra_tops 的填充 = 主文件顶层按源码序、**import 语句就地递归展开**（被
导入文件顶层项插在 import 位置）+ 泛型展开/方法收集追加尾部 → 源码级交错
序（= tig_ast 处理序）。「模块 0 片段函数 + 模块 k 片段函数…」的拼接序在
主文件函数位于 import 之后时不成立（例：`import a; func main()` 的正确序
= [a 项, main]，拼接序 = [main, a 项]）。装配器按 §8.1 的 g_extra_tops
驱动 + 合成函数头/尾识别（主片段函数序中首个属于 g_extra_tops 名集的函数
之前 = 头部合成、其后 = 尾部合成，均保序）实现。实现骨架不变。

## 9. p.9.21.9 片段组装消费 —— 落地记录（2026-09-24）

落点：tieir_asm.tie（装配器 ~560 行）+ driver/pipeline.tie（kpass_irgen 全命中
装配挂点 + asm_build_order 取名）+ cache_drv（mod_slice_key 抽取 +
modcache_assembly_paths）+ driver.tie import。不动点 8292cfa5 → **f2ef82df**。

* 装配路径：kpass_irgen 入口全命中判定（dep_depset 逐模块键存在）→ 跳过
  irgen.tig_ast + passes.run → tieir.asm_from_slices（解析段 3/5 转存 →
  g_extra_tops 序驱动重放）→ TIEC_INC=1 打印 MODASM h/n assembled。装配
  失败响亮降级全量（MODASM fallback 打印）。
* **llvmgen 置位副作用恢复**：irgen 生成引用时对 llvmgen 置位（sso_enable/
  catch_enable/wsock_enable）——装配路径按片段 IR 白名单全局名引用等价恢复
  （asm_flag_sso/wsock/catch，白名单对齐 llvmgen_inst_p1：s21_sso_*、
  g_wsock_init、tie_panic_jb/active）。**遗留**：全局 var 登记类
  （global_table_reg/global_scalar_reg/global_scalar_init/call_sym_reg/
  vtable_reg/tbl_inlined_check）未恢复——含顶层 VarDecl 的工程装配后 exe
  编译会缺全局定义；探针工程（无用户全局 var）不受影响。恢复路径下轮：
  AST（g_extra_tops tag 100）重放登记或片段头携带登记数据。
* **验收数据**（探针工程 d1 菱形 4 模块，全命中装配）：
  - MODASM 4/4 assembled；装配 IR → llvmgen/opt/link 全链成功；
  - 装配 .tir vs 全量 .tir：段 2/4/6/7 **逐字节一致**；段 5 大小一致
    （10120B）、内容 DIFF = 池 id 排列连锁（池段本身 DIFF 4320B vs 4656B，
    装配池少 irgen 期间的临时串）——**§8.2 口径再修正**：池 id 是进程内
    句柄且段 5 内嵌池 id，故「段 5 逐字节」受池序连锁影响，语义等价以
    **dump_text 对比**验证：`DUMP IDENTICAL`（独立进程各自 deserialize +
    dump，含包/依赖/函数/块/指令/值规模与符号/导出明细）；
  - 勘误：§7 span「编译器零调用点」结论不变，但 write_mod_slice 段 7 写入
    的 span 行为**全 0 冗余**（读 inst_line 默认值）——装配器已改为跳过
    span 段（不转存不写回），全量侧恒空 → 一致。
* **基线变更（良性）**：regress 由 157/8/2 → **158/7/2**。7b7d8886 /
  8292cfa5 / f2ef82df 三版 tiec 实测 FAIL 集合完全一致（generics、
  proc_createprocessw_pipe、std_httpc_probe、std_net_bytes、std_net_text、
  std_sse_probe、table_struct_elem——网络/FFI/泛型类已知项），第 8 个
  FAIL 为 exec 竞态偶发项，p.9.3.9 语句序修复 + 移除 sleep_ms 后消除。

## 10. p.9.17.1 str_char 码点索引缓存 —— 实施进度与卡点（2026-09-24）

基线实测（铁律 3）：str_char 编译路径 O(n²) 确认——100K 码点 char-wise 遍历
>120s（被命令时限杀）；10K ≈ <1s；interp 路径 10K ≈ 1s（~100µs/char）。
prompt 的 ~360µs/char 数字与 interp 路径量级吻合，编译路径 O(n²) 步进在大串
下同样是灾难。

实施（工作树未提交——IR 生成正确性调试中期）：
* irgen_bi_num.tie：bi_str_char 重写为**单槽缓存版**——@tie_sc_addr/len/n/tab
  四全局（[131072 x i64] 偏移表）；命中 O(1) 读表、未命中单次 O(n) 重建；
  i >= CAP 回退 legacy 线性循环（行为兜底）。llvmgen：白名单加 tie_sc_* +
  emit 四全局（.bss 零成本）。
* 已修渲染坑：store 必须**三操作数** [ty IMM, 值, 地址]（llvmgen
  gen_inst_b_22_store 约定）；kind 3 全局直引不可走 tig_p2i（硬编码 kind 0
  → 渲染 %N）——须手写 op24 ptrtoint + kind 3 操作数；cond_br 必须
  [cond, true, false] 全三操作数；**块创建序必须 = 控制流逻辑序**（llvmgen
  按块表序输出，值 id 回退 → opt 报 numbering 错）。
* **当前卡点**：s21_utf8_seq_len 内联（重建循环体内调用）的块群嵌在
  sc.rb_body/sc.rb_cond 循环回边下，opt 报 `%277 = zext i1 %361` 编号回退
  （seq_len 展开的块创建序与其值 id 序在循环上下文交错）。下一步：勘察
  s21_utf8_seq_len/s21_utf8_char_at 的块结构（frontend 系 helper 是否假设
  「调用点为线性块尾」），或改为重建循环内**不经 seq_len helper**（手写
  seq_len 判定内联块，控制创建序），或缓存重建循环整体迁到运行期 helper。
* 缓存正确性论证不变：串不可变 + (ptr, len) 键；行为一致性由 tab = 内容
  确定性函数保证。
* 验收命令就绪：_tiec_verify/bench_strchar1m.tie（100K 码点，基线 >120s）
  / bench_sc100.tie（100 码点冒烟）；tsh 路径 bench_tsh3.tie。

### §10.1 补记：str_char 缓存回滚与自举连锁（同日）
缓存版 irgen（工作树）触发**自举连锁失败**：bootstrap [2/4] 写 driver 片段 →
[3/4] 全命中触发装配 → 装配器缺全局 var 登记族（已知遗留）→ llvmgen rc=2。
同时第二层产物暴露缓存正确性 bug：**交替串/非遍历调用场景**（config 参数
解析的 str_char 调用点）返回错值（acc 差 106 = 丢最后码点；根因 = 重建循环
退出时 @tie_sc_n 差一——phi 退出值语义 + 交替串缓存失效组合，trace/acc/
多字节三组对照已定位）。**裁定**：回滚 irgen_bi_num/llvmgen/llvmgen_str/
llvmgen_inst_p1 的缓存改动（git checkout，findings §10 保留全部设计/坑/
出路）；pipeline.tie 加**装配护栏**（含顶层 VarDecl 单元 → 空 order → 诚实
降级全量，自举 [3/4] 即此场景——已实测修复）。不动点 f2ef82df →
**6e836504**；regress 158/7/2 一致。下轮：交替串 bug 最小复现 → 修 phi 差一
与单槽交替失效 → 重上缓存。

## 11. p.9.21.9 收口：装配路径副作用恢复 + 装配器四处缺陷（2026-09-25）

落点：tieir_asm.tie（装配器）/ tieir_slice.tie（片段写护栏）/ llvmgen.tie
（has_global + reset_global_regs）/ irgen.tie（asm_reg_globals/asm_reg_msg/
asm_reg_rng/asm_is_libc）/ driver/pipeline.tie（护栏摘除 + asm_side_recover）/
driver.tie（asm_recover_err + 盐 v5）。不动点 6e836504 → **19f11c25**
（n1=n2=n3，certutil 直核一致）。

### 11.1 全局 var 登记族恢复（原遗留，已摘护栏）
装配路径跳过 irgen → llvmgen 全局段/vtable 段无人登记。按「AST（g_extra_tops）
+ 语义层仍在，片段 IR 是唯一事实」两条腿恢复：
* `irgen.asm_reg_globals()`：reg_all_vtables（impl 记录）+ 顶层 VarDecl
  （tag 100）+ 命名空间 const（tag 112 内 tag 100，全名 prefix::NAME）——与
  tig_ast/tig_ns 同序遍历重放（只登记，不生成 IR）。
* `asm_side_recover()`（driver）：按片段引用的全局名恢复惰性登记族
  （msg_* 四槽 / @__rng_state / Linux 入口 @__tig_argc,argv）与
  p.6.10.4 循环哨兵（@tl_loopf_*：i64 零值，名字含函数名+序号，前缀识别）、
  链接判据（g_used_wsock / trmlite），并做**登记完备校验**：引用的全局既未
  登记又不属于 llvmgen 旗标段 → 返回 -1 降级全量（不静默产缺全局的单元）。
* 全局名在 IR 里带/不带 `@` 两种写法并存（实测 s21_sso_off 为裸名）→ 置位
  白名单与校验一律按裸名比对。
* 降级前 `llvmgen.reset_global_regs()`（否则全量路径二次登记同名全局 → .ll
  重复定义）+ 链接判据复位。

### 11.2 装配器四处缺陷（本轮实测修正）
1. **块操作数域错**：kind 1 载荷 = 片段内块 lid（write_mod_slice 写
   blk_new[ov]，跨片段全部选中函数连续编号），旧实现按「函数内序号」解 →
   多函数片段必然越界/错位（探针 gv 首跑报 `块操作数越界 fn 1 lid=121`）。
2. **块/指令按函数分组假设不成立**：块表内同函数的块可能交错（闭包/嵌套生成）
   → 改显式分组（asm_fb_idx 前缀和段 + asm_bi_base/cnt 逐块区间）。
3. **值基址口径偏大**：旧「观测最小值」在参数未被引用时 ≠ f_vbase → 值偏移
   整体错位。改为按 vsize = 参数数 + 结果数 累计复现（与 write 的 vcum 同式）。
4. **值映射改显式表**：asm_vmap（片段值 id → 重放值），取代 per-fn 结果表 +
   偏移运算（与值域是否交错无关）。

### 11.3 新缺陷 D5：块指令区间交错（未根治，已加护栏）⚠ 立 p.9.21.10
`ir.new_block` 的 [start,end) 区间在 irgen **交错建块**（A 未闭即建 B 再回 A）
时互相跨越：driver 全量 .tir 实测 **22515/74631 块非单调**（例：块 13 =
[244,250)、块 14 = [231,234)）。write_mod_slice 按 [start,end) 逐块写会
**重复/错序**指令 → 装配单元必然错（离线核查 driver 片段共 **910 处前向值
引用**，即重复指令的表象）。
* 单趟不可改两趟：`ir.add_operand` 断言操作数段紧接段尾（ops_off 在 new_inst
  时定），延迟补操作数必撞「操作数段交错」panic（已实测）。
* 本轮护栏（诚实降级）：write_mod_slice 拒绝写入「选中块区间重叠/乱序」的模块
  片段（driver：217 模块仅 48 可写 → 装配路径不命中 → 全量 irgen）。
* 根治方向（p.9.21.10）：片段改**按指令 id 序**写 + 逐指令显式块归属（段 5
  指令表增块 lid 列 / 块表改记首指令 id），或让 irgen 单调建块（大改，风险高）。

### 11.4 验收与基线口径
* VarDecl 探针（tests/_modcache_probe/gv1..gv4：标量全局 + 表全局（含非空表
  字面量初值）+ 命名空间 const + 菱形导入）：**MODASM 4/4 assembled**，装配
  路径 exe 与全量路径 exe **stdout 逐字节一致**。
* driver 树：护栏生效（48/217 可写）→ 装配不触发，全量编译通过（39s）。
* 回归：**157 PASS / 8 FAIL / 2 SKIP**。第 8 个 FAIL = `extern_s10_ptr`——
  **陈旧缓存假象**：该测试需 tie_interp.lib（本机已无，0-Rust 后环境缺），
  基线 158/7 里的 PASS 来自旧缓存产物（含该 exe 的编译期产物副本）；冷键下
  **基线编译器同样 COMPILE_FAIL**（已用 6e836504 与 2e902195 两版直核复现）。
  故冷缓存真基线 = 157/8，非本轮改动回归。
* 盐 v2 → **v5**（装配器语义 + 片段写入口径变更，旧片段必须整体失效）。

## 12. p.9.17.1 str_char 码点索引缓存 —— 重上落地（2026-09-25）

落点：llvmgen_sc.tie（新文件：emit_sc_globals——@tie_sc_addr/len/n/tab 四全局
（双槽各 1MB .bss）+ @tie_sc_off / @tie_sc_inval 手写 helper）+ llvmgen.tie
（sc_enable 旗标 + 发射挂点 + sc 启用强制 SSO 段）+ llvmgen_p1.tie
（@tie_str_free_if_heap 加失效钩子）+ irgen_bi_num.tie（bi_str_char 重写）+
tieir_asm.tie（asm_flag_sc）+ driver/pipeline.tie（sc 恢复）。不动点
19f11c25 → **0cf19245**；盐 v6；回归 **157/8/2** 一致。

### 12.1 架构（与 §10 已验证方案同源，坑全绕开）
* **helper 单体**：缓存命中判定、双槽选择、重建循环、CAP 兜底 legacy 线性
  步进全部在**手写 LLVM**（@tie_sc_off(s, i) → 字节偏移或 -1）；irgen 只发
  一次 call + 两个线性块（bad/ok/merge，复用既有 s21_utf8_char_at 解码 +
  s21_codepoint_to_str 构造）。**irgen 侧零循环块**——旧实现的
  「seq_len 内联嵌在重建循环回边下 → opt numbering 回退」卡点从结构上消失。
* **phi 差一修正**：@tie_sc_n 存循环 phi 的 %k（= 已写项数，rbd 处 phi 出口
  值即正确），旧实现「存退出时 phi %k」的语义歧义不复存在。
* **交替串失效修正**：双槽按 (addr>>3)&1 选槽（串指针 8 对齐，bit3 随分配
  翻转）——交替对稳定落双槽，零 LRU 成本；3 串以上轮转退化为逐调用重建
  （正确性不变，代价 = 旧 O(i) 步进上限）。
* **陈旧命中防御（新）**：malloc 同址同长复用会让 (ptr,len) 键命中错表 →
  @tie_str_free_if_heap free 前调 @tie_sc_inval(数据指针)，清匹配槽。
* **越界语义与旧实现逐位一致**：i 超码点数 → -1 → 空串；i<0 → legacy 路径
  返回 offset 0（首码点，与旧实现怪癖一致）。

### 12.2 实测坑（本轮新增）
1. **字符串值指针指向数据**，长度头在 **s-8**（s21_str_head_len = gep(s,-8)）
   ——helper 初版按 {len@0,data@8} 读 → 全错位。gelp 基准一律数据指针。
2. **icmp 比较码**：0=eq 1=ne 2=slt 3=sgt **4=sle** 5=sge 6=ult…——
   `tig_cmp_zero(off, 4)` 是 **sle**（off=0 会被判负）；sub_bytes 处旧注释
   「slt」系笔误（该处 clamp 语义恰好兼容）。判负必须 cc=2。
3. **LLVM 多维数组语法**：`[2 x [131072 x i64]]`（`[2 x 131072 x i64]` 报
   expected type——第二位必须是类型）。
4. `sc_enable` 时 emit 侧强制 `g_sso_enabled=1`：@tie_str_free_if_heap（失效
   钩子宿主）随 SSO 段发射，保证缓存存在则钩子必在。

### 12.3 验收数据
| 项 | 基线 6e836504 | 缓存版 0cf19245 |
| --- | --- | --- |
| bench_50k（50K 码点顺序遍历） | 4ms，acc=57 | **0ms**，acc=57 |
| bench_sc_last（100K 恒取末码点，最坏 O(i)） | 38ms，acc 同 | **0ms**，acc 同 |
| bench_mb（多字节） | acc 一致 | acc 一致 |
| scprobe（ASCII+多字节+越界+负索引 9 例） | — | **stdout 逐字节一致** |
| scalt（双串交替正扫+反向扫） | — | **stdout 逐字节一致** |
| 回归 | 157/8/2（冷口径） | **157/8/2** |
| 三阶自举 | — | FIXED-POINT OK（n2=n3，直核） |
| 库自检 ×4 / trm 探针 | exit 0 / PASS | exit 0 / PASS |

**基线数字勘误（铁律 3 再验证）**：§10 的「编译路径 O(n²)、100K>120s」基线
已失效——现基线顺序遍历 100K 仅 19ms、恒末码点 38ms（§10 测量时的条件与
今日基线不同；prompt/旧 findings 的性能数字动笔前必须重测）。

### 12.4 装配路径联动
asm_flag_sc：片段含 `call @tie_sc_off`（op 35 载荷白名单）→ driver 恢复
sc_enable（emit 侧隐含 SSO 段）。gv 装配探针复测 **4/4 assembled、stdout
逐字节一致**（不受本轮影响）。

## 13. p.9.21.10 落地：写侧块归属统一 + 三个潜伏缺陷修正（2026-09-25）

落点：tieir_ser.tie（serialize 游标修正）+ tieir_slice.tie（write_mod_slice
按指令 id 序写 + 值域跨度压缩）+ tieir_asm.tie（重放单趟化 + 片段值全局基址
+ pty_base 哨兵移除）+ driver/cache_drv.tie（部分列表修正 + 写失败诊断）+
ir.tie/irgen.tie（C' 断言实验与回退）。不动点 0cf19245 → **825f97fd**（盐
v8）；回归 **157/8/2**；三阶自举 FIXED-POINT OK；库自检 ×4 / trm 探针 / gv
装配探针全绿。

### 13.1 方案落地（对齐讨论定稿：A + 写侧统一归属）
* **serialize 游标修正**：原单向游标在「块表序 ≠ 指令 id 序」时越过目标块
  再不回头——driver 全量 .tir 实测 **663730/663974 条指令 own == block_count
  （越界值）**，块归属几乎全错（此前无人发现：消费者浅、且乱序单元从未
  roundtrip 过）。改为归属表：每块回填自己的区间（O(ni)），own 恒正确。
* **write_mod_slice 改按指令 id 序（= 创建序）单遍写**：own = 真归属块新
  id；块表 start/end = 新流中位置（各块指令在 id 序下连续）。值域压缩基数
  从「计数」改「**跨度**」（v_max - v_start + 1）——交错生成时他函数值会插
  进本函数值域内部（span > count），按 count 累计使相邻函数片段值域交叠
  （vmap 键碰撞 → 装配错值，driver 实测 putil::slice_str 参数全部错位）。
* **装配器重放单趟化**：片段指令流已是创建序 → 按**全局指令流单趟**重放
  （建指令即补操作数），替代按函数两趟；`asm_i_blk` 回归（挂块用）。
* **片段值空间全局基址（asm_frag_vbase / asm_frag_vtotal）**：各片段值 id
  独立从 0 压缩，而 vmap 是全局键空间——必须加片段基址才唯一。旧两趟重放
  按「片段顺序登记→使用→下一片段覆盖」的时序侥幸成立；单趟重放（全片段
  注册先于使用）立即引爆（实测 @ast$tag 参数存引用错值）。
* **modcache_assembly_paths 部分列表修正（关键安全修复）**：任一片段缺失
  时原 `return out` 会把**已累积的部分列表**带回 → 装配器拿残缺片段集静默
  装配 → 缺失模块的函数全部未定义符号（driver 实测 218 模块缺 21 个、
  regress 138/27）。改为返回空表（与头注文档语义对齐）→ 诚实降级全量。
* **写失败诊断**：mod_cache_update 写失败不再静默（TIEC_INC=1 打印模块与
  err_msg）。

### 13.2 C' 断言实验：前提证伪，回退
曾实现「块区间连续断言」（块未闭只许段尾追加，违例 panic），driver 通过但
闭包探针当场炸出：**irgen 回填（块 A 未闭 → 闭包块领号 → 回填 A）是合法
模式**，且 llvmgen 的 `build_inst_blk`（区间回填、表序后者覆盖）+ 按指令
id 序发射早已正确处理交叠。断言使闭包程序无法编译（regress 138/27）→
**回退**。教训：不变式先在消费者全集上验证再上升为断言。

### 13.3 附加发现：asm_f_pty_base 尾哨兵越界（2f0e14 潜伏缺陷）
`asm_f_pty_base[n] = len(asm_f_pty)`（n = 片段数）写在**函数记录索引**的
表上——片段数 ≥ 函数记录数时越界改写该记录的类型基址 → 其参数类型全部读
零（driver 实测 putil::slice_str (ptr,i64,i64) → (i8,i8,i8)）。小探针
（记录数 < 片段数）永不触发。哨兵无消费者，移除。`asm_f_base[n]` 保留
（该表确为片段索引，len = n+1）。

### 13.4 验收数据（driver 树，全部片段装配 218/218）
| 项 | 全量路径 | 装配路径 |
| --- | --- | --- |
| 编译 driver.tie 全程 | ~55s | ~57s（**基本打平**） |
| —— kpass_front | 5.3s | 5.7s |
| —— kpass_irgen | 3.4s | 13.6s（片段解析+重放） |
| —— kpass_emit / link | 14.9s / 29.4s | 14.2s / 22.3s |
| 装配版编译器跑 regress | 157/8/2 | **157/8/2（完全一致）** |

**⚠ 勘误（同日更正）**：本节初稿「装配 ~20s vs 全量 ~35-40s」系**测量假象**——
那次 19.8s 的装配跑在 opt 阶段失败退出（未付 ~25s 链接账），被误与全量成功
跑对比。GetTickCount 分段实测（上表）：两路径全程 ~55s 打平；**driver 规模下
装配路径净负收益**（重放 13.6s > 跳过的 irgen 3.4s）。收益大头在 emit(14s)+
link(22-29s)（两路径相同）与产物级命中（cache_try_hit_dep 直接复制 exe）。
装配路径要转正需压重放成本：片段格式二进制紧凑化（现状逐字段 i64 + 字符串
8B/字符，218 片段 ~百 MB I/O）、按需解析、或池/指令段 memcpy 化（另立批次）。
| gv 探针装配 | — | 4/4 assembled、stdout 逐字节一致 |
| trm 探针 / 库自检 ×4 | — | PASS / exit 0 |
| 三阶自举 | — | FIXED-POINT OK（0cf19245 → **825f97fd**，盐 v8） |

**遗留**：片段池段仍按写侧口径允许排列差异（dump_text 口径不变）；
`build_inst_blk` 的覆盖式归属与序列化/片段写侧的三处独立实现可在后续统一
为单一归属工具（性能中性，纯去重，未列入本期）。

### 13.5 性能转正尝试（同日）：分账与结论
GetTickCount 分段实测（PHASE/ASMDIAG 计时已进管线，TIEC_INC/TIEC_ASMDBG 门控）：
* **parse 4.8s**（73.7MB 片段字节；rd_i64 逐字段 8B + rd_str 逐字符 8B +
  str_from_code 逐字符 SSO 分配 + O(n²) 拼接）+ **seq+replay 9.4s**
  （build_seq 两处 O(order×records) 字符串扫描已改 interner id 直接索引
  O(1)，实测仅省 ~0.3s——字符串比较不是大头；主体 = 664K new_inst +
  3M add_operand 的 ir API 调用）。
* **三趟批量重放实验**（建指令 → 原地 remap → ir.ops_append 整表接续 +
  set_inst_ops_meta 回填）引入 ast 片段 fm2 归属错位（残缺 vmap 键 → 错值），
  未能在本批定位，**回退到逐条 add_operand 版**（byte-identical 已验证）。
  留下的响亮诊断（remap 未登记即报错）是下批的现成起点。
* **结论**：装配路径端到端 ~57s vs 全量 ~55s，driver 规模下暂为净负
  （重放 9.4s > 跳过的 irgen 3.4s）；**大头是 emit 14s + link 22-29s
  （占 ~75%，两路径相同）**。转正路径 = 片段格式二进制紧凑化（u32 字段 +
  UTF-8 字符串，字节量 ~4-8×↓）+ ir 批量 API 完成化，目标 parse+replay
  ≤ 3.4s；另 emit/link 的缓存化是更大的独立命题。正确性基础设施（218/218
  装配 + 装配版编译器 regress 完全一致）本批已闭环。

## 14. p.9.21.11 片段格式 v3 + 装配覆盖三缺陷（2026-09-26）

落点：tieir_fmt_v3.tie（新文件）+ tieir_slice/tieir_asm（v3 读写对）+ tieir_test
（roundtrip 改走装配路径）+ pipeline（asm_order_one_fn）+ cache_drv（键加单元根）
+ driver.tie（盐 v9）。不动点 825f97fd → d31ddb74（中间升格）→ **4a04bb9a**；
回归 **157/8/2**（全量 + 装配版一致）；库自检 ×4 / trm 探针 / gv 探针 4/4
stdout 一致；三阶自举 FIXED-POINT OK（certutil 直核）。

### 14.1 v3 格式（只动片段读写对；全量 v2 不动）
* 字段 **u32 小端**；kind 2（立即数）操作数载荷 **i64 LE 8B**（全值域）；可能
  取 -1 的字段（fn ret/entry、inst ty/val、blk start/end、sym/exp 行列）+1
  偏置，哨兵 0x7FFFFFFF → i64 LE 逃逸；字符串 = u32 字节长 + UTF-8
  （string_builder 逐字节累积 + 一次 sb_build——消灭 rd_str O(n²) 拼接与
  逐字符 SSO，敌人 #5/#6）；操作数序改 **[kind, payload]**（payload 宽度
  依赖 kind）；段 7（span）移除（恒全 0 冗余，findings §9 勘误）。
* **D6（新，写入侧）**：op36 extern_call 的 ins_ty 槽在活体 IR 中带
  7696581394432 量级野值（v2 8B 容得下无人发现）。首版 wr_u32p1 越界仅
  set_err 不中断 → 字节流错位且 bytes.write 仍"成功" → 装配端在远处炸
  （"池载荷越界 46"），定位极难。修 = 逃逸编码 + 写侧任一错误立即中止。
  教训：**写侧错误检查必须内联在写入循环里，"set_err 后继续写"等于埋雷**。
* **D7（新，读取侧）**：asm_bare_name 逐字符拼接 O(n²) → str_sub_bytes
  单次拷贝（池载荷热路径）。

### 14.2 装配覆盖三缺陷（driver 219/219 的拦路虎）
* **D8 同名记录单槽**：a7d4211 的 build_seq O(1) 改写用 name_rec 后写覆盖，
  同名 ≥2 条记录（跨模块泛型展开）时后者永不匹配 → 改 head/tail 链表
  （FIFO 对齐旧线性扫描语义）。
* **D9 展开不在装配序**：asm_order_one_fn 见 TYPE_PARAMS 首槽即跳过，而
  sgen_inst 的展开 clone（clone_subst 深克隆）保留该槽 → 展开永远不进序。
  但展开经 fn_sig 归属到来源模块片段 → 覆盖校验必炸。进一步勘察发现
  **irgen 期兜底实例化**（instantiate_fn 在 irgen 遍历中追加 clone）发生在
  装配序构建之后——**装配序快照原理上不可能含 irgen 期展开名**（注册表
  补名方案同样无效：登记也发生在序构建后）。终修 = build_seq 加 **extra
  段**：未匹配非主片段记录按记录序插到 matched 后、tail 前——与 tig_ast
  创建序一致（原始顶层 → 遍历中追加并由同一遍历取用的克隆 → 尾部合成）；
  重放函数表序不影响语义（值/块/指令空间 per-function + per-fragment 基址，
  与重放序无关）。基线二进制 d31ddb74"219/219"系**陈旧 v8 片段假象**
  （旧归属形态的遗留片段），不可作为对照。
* **D10 片段键跨上下文污染**：模块 IR 含上下文相关泛型展开（任一调用方的
  实例化归属到模板来源模块），而 mod_slice_key = path|fp|salt|t|target
  **不含单元根**——regress 测试工程写的 std/string.tie 片段（含 expect_eq
  展开 + 对 test::expect 的调用）被 driver 装配命中（键同、命中不覆写），
  test::expect 在 driver 单元无定义 → opt 报 use of undefined value
  @test$expect。修 = 键加 "|R" + k_g_src（单元根主源路径；compile_program
  入口赋值，读写两侧均在赋值后）。键格式变更即整体失效，无需另 bump 盐。

### 14.3 验收数据（driver 树 219 模块，R 键隔离后）
| 项 | v2（基线） | v3（本次） |
| --- | --- | --- |
| 片段字节总量 | 73.7MB | **30.2MB（2.4×↓）** |
| ASMDIAG parse | 4.8s | **1.8s** |
| ASMDIAG seq+replay | 9.4s | **5.2s** |
| kpass_irgen（装配路径） | 13.6s | **7.2s** |
| driver 装配 | 218/218（陈旧片段口径） | **219/219（R 键隔离、新鲜片段）** |
| 装配版编译器 regress | 157/8/2 | **157/8/2** |
| 三阶自举 | FIXED-POINT OK | **OK（4a04bb9a）** |

**转正判据（§3）未过，诚实记录**：parse+replay = 7.0s > 目标 4s（跳过的
全量 irgen 仅 3.4s）；装配路径端到端仍略负。剩余成本大头 = replay 侧
664K ir.new_inst + 3M ir.add_operand 跨命名空间逐条调用（三趟批量实验
曾引入 fm2 错位已回退，需 ir 批量 API 完成化后再攻，另立批次）。片段
字节已 2.4×↓，parse 侧转正已达（1.8s < 3.4s 全量 irgen）。

### 14.4 工具备注
* `_tiec_verify/slicedbg_v3.py`：v3 片段离线解剖器（段级边界校验）。
* 铁律 11 扫描（§0.5 清单口径）：新增 tieir_fmt_v3.tie 315 行 ✓ ≤500；
  tieir_asm.tie 891 行 ⚠ 超 500（存量 +本轮 +130，拆解随 §5.0 批次）。

### 14.5 §2.5 str_len 双槽缓存（同日补完，用户钦定项）
* 落点：llvmgen_sc.tie（@tie_sl_addr/blen/val 三全局 + @tie_sl_len 手写
  helper——(ptr, blen) 双槽键 + O(blen) 步进计数 + 命中 O(1)；无 CAP——
  len 缓存无 per-string 大表；@tie_sc_inval 扩为同时清 sl 槽）+
  irgen_bi_num.tie bi_str_len 重写（内联 4 块循环 → 一次 call @tie_sl_len，
  每调用点码量 3253→926 字节）+ tieir_asm asm_flag_sc 白名单加 tie_sl_len。
* 语义：与旧内联循环逐位一致（返回码点数，空串 = 0）；双槽 (addr>>3)&1
  选槽覆盖交替串对；free 钩子失效防 malloc 同址复用陈旧命中（与 str_char
  同机制，findings §12）。
* 验收（bench_strlen.tie / bench_strlen_alt.tie，新旧编译器输出逐字节对照）：
  | 场景 | 旧（内联循环） | 新（缓存） |
  | --- | --- | --- |
  | 50K 码点串 str_len × 100K | 20ms（opt LICM 已外提） | **0ms** |
  | while i < str_len(s) 遍历 | 10ms（同上） | **0ms** |
  | 双串交替 50K 次（ASCII+多字节） | — | 与旧版逐字节一致 |
  | 多字节/空串边界（9 码点/0/200） | true | **true** |
  诚实记录：本 bench 场景 opt LICM 已把循环不变 str_len 外提，旧版基线偏弱
  （20ms 而非理论秒级）——缓存的真实收益在 opt 提升不了的场合（跨调用、
  字符串非循环不变）；正确性由新旧输出逐字节一致背书。
* 不动点 4a04bb9a → **02990dd8**；回归 157/8/2 一次过；库自检 ×4 / trm /
  gv 4/4 stdout 一致；driver 装配复验 219/219（parse=2.2s / replay=5.5s，
  与 4a04bb9a 持平，无回归）。
* **批量重放实验（同日，回退）**：bulk 表 + ops_append + ops_meta_bulk 版在
  driver 规模 >110s（v3i 逐条版 7.0s），且与产物缓存命中状态翻摆纠缠（成功
  /超时交替），本地无法稳定归因——按铁律 4 整体回退到 v3i 已验证形态；
  ir.ops_append（此前已提交）保留，ops_meta_bulk 随实验撤除。批量方向留
  专项勘察：嫌疑 = 大表按值传参整表拷贝（铁律 11 #7）与缓存翻摆交互。

### 14.6 批量重放勘察补充（同日第二轮，仍回退；为下一轮留下硬数据）
* 二次实验（bulk 恢复 + 分段 file_append 标记——**标记必须带 tick 且写文件
  而非 stdout**：stdout 全缓冲，被杀进程的 PHASE/ASMDIAG 输出全部丢失；
  另 TIEC_ASMDBG env 三次忘设——测量脚本必须固化 env（run_asmdbg.sh 范式））：
  * **干净实测（v7，markers 完整）**：parse 219 片段 2.3s；bulk 重放循环
    4.9s（inst 级耗时 3.5→12µs 随 bulk_v 增长劣化）；ops_append 157ms；
    ops_meta_bulk 62ms；**asm_from_slices 完整返回（count-ok）**——
    bulk 重放本体不慢、不挂。
  * **~100s 消耗在 count-ok 之后、emit 完成之前**（26MB .ll 最终产出，
    进程 ~110s 未退出）——未插桩区段 = asm_side_recover / 旗标 / llvmgen
    emit-on-assembled-IR，下一轮先在此三分段插桩。
  * **「翻摆」机制勘破**：重编译改 middle/driver 源码 → fp 变 → 该模块片段
    键失效 → ap 空 → 全量路径（16-21s，exit=0）→ 顺带写齐片段 → 次跑
    ap 命中 → 装配路径 → 慢。所谓成功/超时交替 = fp 失效循环，非缓存
    非确定性问题；每轮测量前必须确认片段集与当前源 fp 一致。
  * **局部表陷阱（新，敌人 #7 实证）**：tie 表值语义下，`table_push(局部表,
    x)` = 整表拷贝再绑定 → O(n)/次；1.3M 槽局部表 push 实测 O(n²)。
    全局表原地推 O(1) 均摊（parse 侧 asm_o_v 同规模 3M 推仅 2.3s 实证）。
    bulk 表必须为全局（本已改全局，仍劣化 → 劣化源另有其人，见上条）。
  * 决定：**维持回退**。转正判据（parse+replay ≤4s）保持未达诚实记录；
    下一轮入口 = 在 asm_side_recover / emit 两个未插桩段先分账，再决定
    bulk 是否恢复（bulk 本体已证可行）。

### 14.7 批量重放终局（14.6 修订，同日第三轮）
* **14.6 两处结论修正**：①「局部表 O(n²) 陷阱」——v7（局部表）与 v8（全局
  表）实测**劣化曲线逐毫秒一致**（704/1359/2078ms per 200K），局部/全局
  并非劣化变量，该结论撤回（table_push 本体均摊 O(1) 有 parse 反证）；变
  慢因子是**环境级非确定性**——v9 全量暖跑（不含 bulk！）、v7/vB 装配跑
  均随机出现 ~5× 放大（111s vs 25s），且被杀进程的 .ll/片段最终完整产出
  （是慢非挂），时间线与 tiec-cache 目录 219 新文件写入后的外部扫描类
  开销最吻合，无法在本地归因到代码。②「翻摆 = fp 失效循环」结论维持。
* **终局**：bulk 重放（全局表版 + ops_append + ops_meta_bulk）实测稳定
  **快于逐条 add_operand**（ASMDIAG seq+replay 7.1s → 5.1s，kpass_irgen
  7.2s），门禁全绿（回归 157/8/2 一次过、tieir_test、gv 4/4 stdout 一致、
  三阶自举 FIXED-POINT OK），**恢复落地**。插桩标记保留（TIEC_ASMDBG=1
  时 file_append 到 phase.log/asmdbg.log，带 tick，进程被杀仍可读——
  本轮定位全靠它）。
* 转正判据：parse+replay = **7.1s（2.0+5.1）**，≤4s 未达，差额 3.1s 在
  replay 侧 664K new_inst + 3M 表推送的本征成本（调用账已消，剩余为
  ir 状态机逐条维护），需 ir 批量构造 API 完成化后另批再攻。
* 不动点 02990dd8 → **4acda07b**。

## 15. §5.1 归属逻辑三处统一 + §5.0 tieir_asm 拆解（2026-09-26）
* **ir_blkattr.tie（新，79 行，namespace ir）**：`blk_attr_fill(n_inst, sel)`
  —— 区间回填、表序后者覆盖（D5 规范语义），交叠/越界计数 + 首个位置经
  访问器读取；sel 空表 = 全部块参与。三处调用点统一：
  llvmgen.build_inst_blk / tieir_ser.serialize 段 5 / tieir_slice sel_of——
  slice 的 D5 拒写语义经访问器逐位保留（错误文案一致）。
* **tieir_asm.tie 拆解（977 → 318/386/307，铁律 11 达标）**：tieir_asm
  （入口 + 全局状态表 + helpers）/ tieir_asm_parse（片段解析）/
  tieir_asm_replay（build_seq + replay）——同 namespace 跨文件。
* **语法发现**：①`type tie<class>` 必须是文件**第一行**（unit 标记），
  注释垫前即解析错；②namespace 体内只允许函数/类/嵌套命名空间，全局
  变量必须在 namespace 外；③跨文件同 namespace 函数/全局需 `pub` +
  显式 import（含 deps-check 方向矩阵）。
* 不动点 4acda07b → **71523177**；回归 157/8/2、tieir_test、gv 4/4 stdout
  一致、三阶自举 FIXED-POINT OK。
* 推送注：隧道对含大二进制的 push 间歇 502/schannel——真因 = 默认
  http.postBuffer(1MB) < 仓库内 6MB tiec.exe；`git config http.postBuffer
  157286400` 后成功（41fff66 实证），后续 502 为隧道自身抖动，重试即可。

## 16. p.9.17.1 续：解释器表追加尾复用 —— O(n²) 清零（2026-09-27）

> 承接 §10-§12 的字符串原语线，轮到同条目里的「容器复制遍历优化」。
> ROAD p.9.17.1 备注「容器 COW/移动语义裁定 v1 维持拷贝」在此**不推翻**：
> 语义仍是值语义（旧节点视图冻结），改的只是存储布局——把「整段复制」换成
> 「尾追加共享起点」，把 O(n²) 降为 O(1) 摊还。

### 16.1 分账（测量先行，禁止凭直觉猜热点）

`tsh_main.exe`，脚本级微基准，各 10 万次迭代，扣除空脚本启动基线：

| 基准 | 循环体 | 净耗时 | 每次迭代 |
| --- | --- | --- | --- |
| D_loop | `i = i + 1` | 230.9 ms | 2.31 µs |
| A_acc1 | `acc = acc + 1` + 自增 | 365.1 ms | 3.65 µs |
| B_accv | `acc = acc + i` + 自增 | 365.4 ms | 3.65 µs |
| E_var | `var x = i` + 累加 + 自增 | 455.0 ms | 4.55 µs |
| C_arith | `acc = acc + i*3 - 1` + 自增 | 528.4 ms | 5.28 µs |
| F_call | `acc = f(acc)` + 自增 | 676.5 ms | 6.77 µs |

读数：**纯循环骨架已是 2.31 µs/次**（含 while 判据的一个比较值分配），每加一个
算术运算 ≈ +1.3 µs，一次函数调用 ≈ +1.8 µs。成本结构由「每 AST 节点一次求值 +
每个值一次 `new_node`（7 张平行表 push）」主导——即 p.9.17.2 拆箱标量的靶子。

本轮不动这条主线，先清**量级更凶的 O(n²)**（分账时撞出来的）：

| 表 push 次数 | 净耗时 |
| --- | --- |
| 4,000 | 473.4 ms |
| 8,000 | 1,818.5 ms |

2 倍 N 得 3.6 倍耗时 → 二次。外推 10 万次 ≈ **298 秒**（实测 30 万次直接顶穿
120 秒工具超时，即此因）。

### 16.2 根因

`value.tie` 的 `table_push_val` 每次 push 把源段整段复制到 `v_kids` 新位置：

```
var n = new_node(T_TABLE)          // 7 张平行表 push
v_koff[n] = len(v_kids)            // 新段起点
while i < cnt { table_push(v_kids, v_kids[off + i]) }   // ← 整段复制
table_push(v_kids, elem)
```

于是 `t = table_push(t, x)` 的追加式建表：第 k 次 push 复制 k 个元素 ⇒
Σk = O(n²) 时间，且 `v_kids` 累计增长也是 O(n²)（内存只增不减的放大器——
按 10 万次估，扁平表要涨到 ~4×10⁹ 项）。

### 16.3 修法：尾复用（语义等价，只是不再复制）

源段末尾正好落在 `v_kids` 末尾时，新段与旧段**共享同一起点**，只追加新元素：

```
if off + cnt == len(v_kids) {
    v_koff[n] = off
    table_push(v_kids, elem)
    v_kcnt[n] = cnt + 1
    return n
}
// 否则回退整段复制（原路径）
```

**安全性论证**（关键，非直觉）：每个段在创建时都是 `[0, len(v_kids))` 内的连续
区间，而追加只影响下标 ≥ `len(v_kids)` 的位置；任何既有段的视图都在其左，故旧
节点只认自己的 `v_kcnt[tid] = cnt`，看不到追加元素——视图天然冻结，与节点新旧
无关。源段不在末尾（多表交叉追加、别名后再追加）时走原复制路径，行为不变。

### 16.4 实测收益

| N table_push | 改前 | 改后 | 加速 |
| --- | --- | --- | --- |
| 4,000 | 473.4 ms | 33.7 ms | 14.0× |
| 8,000 | 1,818.5 ms | 53.1 ms | 34.2× |
| 20,000 | 11,915.6 ms | 110.0 ms | 108.3× |
| 100,000 | ~298 s（外推） | 442.4 ms | ~674× |

改后随 N 线性（4000/8000/20000/100000 = 33.7/53.1/110.0/442.4 ms），二次项
已消失；微基准 D/A/B/C/E/F 前后中性（±10% 抖动，未触碰该路径，符合预期）。

### 16.5 门禁（全绿）

* **三阶自举不动点**：`d0f36172…` → **`bbb2746a…`**，`compiler/tiec.exe` 已升格。
  升格前先直核「HEAD 基线不动点 == 入库 tiec.exe == d0f36172…」，确认链条自洽。
* **回归**：`regress-s21` = PASS 157 / FAIL 8 / SKIP 2，FAIL 集合与**全量日志逐行**
  与基线一致（基线 157/8/2 与 ROAD 记载相符）。
* **tshell 冒烟**：9/9 逐字节一致（stdout + 退出码）。
* **解释器专项**：`tests/interp/*.tie` 11 个行为套件，旧 interp（fp_head/n3.exe）与
  新 interp 输出**逐字节一致**（含各自的既有 FAIL 行：interp_strings 6、
  interp_table 2——非本次引入）。
* **别名/段视图语料**（新增，专为本次改动的不变式）：冻结别名、交叉追加、
  空表/单元素、300 元素、字符串表、函数间往返 —— 逐字节一致。
* 微基准前后中性；`git diff` 仅 `value.tie` + `tiec.exe`。

### 16.6 操作台踩坑（两个，均为调用姿势而非代码缺陷）

1. **`bootstrap-fp.tsh.tie` 的输出目录必须是反斜杠路径**：脚本内部走
   `cmd /c`，而 Windows cmd 对 `../` 正斜杠命令行路径不可靠——传
   `../_tiec_verify/fp` 会在 [2/4] 报「n1 自编失败 rc=1」（`>nul` 吞掉了真实
   报错，极易误判为自举断档）。传 `..\_tiec_verify\fp` 即 `FIXED-POINT OK`。
   直核：手工用 n1.exe 编 driver.tie 是成功的——**先怀疑调用姿势，再怀疑代码**。
2. **长命令别接管道**：`python -u … | tail -20` 在超时/被杀时缓冲输出全丢，
   看起来像「什么都没发生」。改重定向落盘（`> run.log 2>&1`）再读文件，并把
   工具超时提到 600~1800 s。

### 16.7 遗留（下一批起点）

* **`map_set` 同款 O(n²) 未动**：它同样整段复制 `v_mkeys`/`v_mvals`。尾复用对
  map **不安全**——`map_set` 的升序冒泡会重排段内既有元素，会改到被别名旧节点的
  视图。可做的安全子集 = 新键严格大于末键（追加即有序，无冒泡）时复用尾段；
  其余仍需复制。立项前先勘察 map 在真实脚本里的热度。
* **`new_node` 7 张平行表 push** 仍是每值固定成本（≈1.3 µs/算术运算），属
  p.9.17.2 拆箱标量主靶。
* **既有破损**：`tests/interp/*.tie` 与 `tests/language/interp_eval.tie` 共 12 处的
  `import "../../interp/interp.tie"` 路径在 `compiler/interp` 目录迁移后**全部失效**
  （E00483）。实测可用的写法是**根相对路径**（`compiler/interp/interp.tie`）或
  `../../../compiler/interp/interp.tie`；相对路径的解析基准不是源码目录，易踩。
  本轮用仓外临时副本跑通这 11 个套件做 A/B 门禁，**未改仓库测试文件**——修复
  12 处 import 属独立小项（顺带该重录 interp_table / interp_strings 的既有 FAIL）。

## 17. p.9.17.3（前半）：变量环境键改 interned id —— 消灭每节点字符串比较（2026-09-27）

> §16 分账显示：解释器每值成本由 `new_node`（7 张平行表 push）主导，**变量名的字符串
> 比较是第二大项**。本轮清第二项；`new_node` 留 p.9.17.2 拆箱。

### 17.1 分账（两次，其中一次被推翻）

第一版基准（K 系列，顶层 var 当 globals）**全部失败**——输出 `变量 'g0' 未声明`：
tsh 的 `eval_script` 不把顶层 `var` 暴露给 `func main` 的作用域。该批 15ms/32ms 的
「极快」数字是无意义数据，**已废弃**（技能铁律：失败的 run 不得与成功的 run 比时间）。

改为同作用域变量数对照（M 系列，10 万次迭代，扣启动）：**同样读段内第 0 个变量**，
作用域从 2 条增到 20 条时每次迭代多 **2.57 µs** ⇒ 单次字符串比较 ≈ **143 ns**，
且成本随同作用域变量数**线性**增长（`seg_find_rev` 从扁平表尾部逐条比较到段起点）。

### 17.2 根因

* `lookup` / `assign` / `var_declared` 都收**字符串**参数，热路径每读一个变量走一次
  `nname_str`（`interner.lookup`，虽 O(1) 但是一次函数调用 + 表读）再逐条比字符串。
* `lookup` 还对**每个活动作用域段**各跑一次 `seg_find_rev`（每次从表尾重扫），
  层数越深重复扫描越多。
* AST 的 `a_names` 本就存 **interner id** —— 热路径天然持有整数，却先还原成文本再比。

### 17.3 修法

* `env` / `globals` / `by-ref` 三类容器键改 **interned id**：`env_nids` / `g_nids` /
  `r_nids` + `r_cnids`；探针由字符串比较变整数比较。
* 新增 nid 入口：`lookup_nid` / `assign_nid` / `var_declare_nid` / `var_declared_nid` /
  `scope_local_declared_nid` / `g_declare_nid` / `g_lookup_nid` / `g_assign_nid` /
  `ref_add_nid`。**原字符串签名全部保留为薄包装**（内部 `intern` 一次），文本入口
  （REPL 绑定 / 脚本参数注入 / 宏参数）零改动即照常工作。
* 热路径（`gen_expr` 的 `N_VAR` / `N_CODE_INTERP`、`exec_stmt_assign`、
  `exec_stmt_var_decl`）直接传 id；**错误文本只在冷分支现调 `nname_str`**——热路径
  不再付文本还原的钱。
* 未命中哨兵由 `""`（ref 槽）统一为 **-1**，与其它查找一致。

### 17.4 收益（交替 A/B、4 轮取最小、扣启动）

A = 仅尾复用（§16 状态），B = 尾复用 + interned id：

| 基准 | A | B | 变化 |
| --- | --- | --- | --- |
| M2（读 1 局部，作用域 4 条） | 491.9 ms | 450.0 ms | **−8.5%** |
| M20（读 1 局部，作用域 22 条） | 735.8 ms | 719.4 ms | −2.2% |
| C_arith（算术循环） | 651.0 ms | 622.1 ms | −4.4% |
| F_call（调用循环） | 808.4 ms | 774.4 ms | −4.2% |

### 17.5 ⚠ 测量教训（本批最重要的一条）

首测**结论完全反向**（新版「慢 7~13%」，M2 501→537、M20 724→822）。原因是
**顺序偏差**：两批数据分别串行测量，被测二进制交替受系统抖动影响；改用
**交替轮询 + 多轮取最小**后结论反转为「新版更快 2~8%」。

规则：**任何 A/B 性能结论都必须交替轮询多轮取最小**，单轮串行对照的数字不可信。
工具留在仓外 `_tiec_verify/p917_ab.py`（交替 4 轮取最小）。

### 17.6 门禁

* 三阶自举不动点 `bbb2746a…` → **`2a32fd57…`**，`compiler/tiec.exe` 已升格。
* 回归 `regress-s21` = **158 PASS / 8 FAIL / 2 SKIP**，与改动前宿主**FAIL 集合一致 +
  全量日志逐行一致**。（注意：当前真实基线是 8 FAIL，比 ROAD 记载的 7 FAIL 多一项，
  系此前漂移，非本次引入；且 `tests/` 下新增探针目录会改变总项数——比对数前后必须
  清理临时目录，否则总数对不上。）
* 解释器专项 11 套件 A/B 逐字节一致；别名/段视图语料逐字节一致。

### 17.7 遗留

* **`f_find`（函数名）仍是字符串线性扫描** —— 每次 `call` 都走，是下一个同族目标
  （函数名同样有 interned id 可得）。下标/字段赋值与闭包捕获路径的若干调用点仍用
  字符串包装（功能正确，未优化）。
* **`new_node` 7 张平行表 push** = 每值固定成本，仍是最主靶（p.9.17.2 拆箱）。
* `tests/interp/*.tie` 等 12 处失效 import（见 §16.7）待修。

## 18. p.9.17.2 第一步（拆箱值模型）—— 两个编译器缺陷 + 一个卡点（2026-09-27）

### 18.1 已修：聚合元素表下标赋值发射非法 `add`（tiec 4be6977）

`t[i] = v`（t 为 table<Enum>/table<Struct>/table<fn>/table<tuple>）编译失败：

    opt: integer constant must have integer type
    %405 = add %enum.Value 0, 0

**根因**：`s21_table_set` 为**每次**元素赋值都发射「扩到 i+1 并补零」的块
（p.9.12.2 自动扩容路径），补零值来自 `t21_zero`；该函数只对 `TK_ANY` 特判，
其余聚合类型落到 `tig_int_lit_ty(0, ty)`——它用 `add <ty> 0, <imm>` 物化整数常量，
对聚合类型非法。块无条件发射，故 `t[0] = ...`（无需扩容）也编译不过。

**修法**：新增 `t21_is_aggregate`（any/struct/enum/fn/tuple），聚合走
「聚合槽 + load」，与既有 `TK_ANY` 分支同形。这是 4c3c0e3 的另一半：那次让
**槽类型**跟随元素类型（pty = elem），本次让**零值**也跟随。

**门禁**：不动点 2a32fd57 → **2fc7e125**（tiec.exe 已升格）；regress 158/8/2，
FAIL 集合同修复前基线；触发件一行差异隔离 + 运行期语义探针（逐槽赋值读回/
计算下标/越界扩容/无 payload 变体/多槽连续/相邻槽保持）全对。

**遗留（未夹带）**：扩容补零的聚合槽是**不确定值**（LLVM alloca 未初始化），
与既有 any 分支同形。真零需 IR 层 `zeroinitializer` 常量能力，另立小项。

### 18.2 卡点：enum case 载荷绑定在**被导入的文件**里一律失效

最小复现（15 行；注意 `type tie<…>` 必须是文件第一行、注释用 `//`、
import 路径带引号——三者缺一都会先撞出别的解析错误掩盖本缺陷）：

    // lib.tie  (tie<class>)
    type tie<class>
    enum Value {
        Nil
        Int(i64)
    }
    pub func ff(v: Value) -> i64 {
        switch v {
            case Value.Int(x):
                return x        // ← error[E00488] 未声明的变量 'x'
            default:
                return -1
        }
    }
    // main.tie (tie<logic>)：import "./lib.tie" + 调用 ff(Value.Int(5))

**已排除**（都实测过）：

* 与 namespace 无关——同文件内的 namespace 正常（`a=5`）；被导入文件里的
  **顶层**函数同样失败。
* 与文件角色无关——被导入文件用 `tie<logic>` 或 `tie<class>` 都失败。
* 枚举模式检查器**确实跑到了**该函数：把解构写成绑定数不符（`case Value.Int(x, y)`）
  在被导入文件里能正确报 E00226。
* 与用法无关——`return x` / `println(to_string(x))` / `var q = x` 全失败；
  枚举作形参与函数内本地构造也全失败。

**触发条件**：只要该 switch 位于**被导入的文件**中。主文件内的同一段代码正常。

**登记/查找键两侧**（供接手直接切入）：

* 登记：`scheck.check_arm_patterns_enum` → `sinfer.lv_insert(sstate.child(p, 1+b), …)`
  （原始子节点值，注释称其为「变量名池 id」）。
* 查找：`sinfer_ie_ie1.infer_expr_var` → `nid = intern.intern(sstate.name_str(id))`。
* 两侧**应当**相等（`s_names` 存全局 interner id，`name_str` 即 `interner.lookup`），
  且语句位 switch 的登记发生在 scheck（`scheck_ie_ie2` → `check_switch_case`），
  表达式位在 sinfer（`infer_expr_switch_expr` 已先调 `check_arm_patterns`）。
* 未验完的假设：`lv_keys` 依赖「按名 id 有序 + 二分查找」，若有序不变式在
  导入展开后被破坏（`lv_keys = s_keys` 别名 / 非有序追加），查找会静默落空。
  下一步建议：加临时诊断打印 `lv_keys` 是否仍有序，以及登记时写入的键与查找
  时的键是否逐值相等（本次会话最后一轮按名字排序位置的试探因生成脚本转义
  故障作废，未取得数据）。

**影响**：本卡点**直接阻塞 p.9.17.2 第一步**——拆箱值模型（enum 标签联合）必须
放在被导入的库里，而载荷提取只能靠 case 绑定。设计 §4.2.1 的选型因此暂时无法
落地；`vval.tie`（690 行，已写好并可单独编译为库）与 parity 探针归档在仓外
`_tiec_verify/p917_wip/`，等本缺陷修复后即接上。

**【已修复 · 2026-09-27】根因（比 §18.2 猜测的 lv_keys 有序性简单得多）**：
import 展开把被导入文件 AST 追加合并进主 AST 表时，`append_ast_mem`
（semantic_p1.tie，内存解析路径）与 `sstate.append_ast`（sstate_q1.tie，协议
文本路径）的子节点填充循环对**一切** `cid >= 0` 的子值无条件 `+base` 当节点
id 平移。而 N_CASE_BIND 的 children[1..] 是 parser 直接 intern 的**裸名池 id**
（非节点 id，ast.tie:179 注释明示；scollect.contains_yield / sgen.clone_inner
均已有同款特判，唯独两条 append 路径漏了）。平移后登记键 = 真 id + base，
查找键 = `intern.intern(name_str(...))` = 真 id → 二分必落空 → E00488。
主文件 base=0 无平移，故只在被导入文件失败——全部症状（含 E00226 结构检查
正常）由此一点解释。

* 修复：两条 append 路径子节点填充循环加 N_CASE_BIND 特判——children[0]
  （变体引用节点 id）照常 +base；children[1..]（裸名池 id）不平移。口径与
  scollect.contains_yield / sgen.clone_inner 对齐。
* 门禁：不动点 `2fc7e125` → **`6d7664af`**（tiec.exe 已升格）；回归
  **158 PASS / 8 FAIL / 2 SKIP** 且 FAIL 集合与基线逐行一致（8 FAIL 均既有
  环境类/已知缺陷）；`tests/interp` 11 套件新旧 exe 输出逐字节一致；
  `tests/language/enum.tie` / `enum_method.tie` 输出符合期望；最小复现
  （单绑定 + 多绑定 `case Shape.Rect(w,h)`）新旧双向验证——旧 exe 两探针均
  E00488，新 exe 均编译运行正确（5 / 12）。
* p.9.17.2 卡点解除：`vval.tie` 作为被导入库编译通过，parity 门禁
  **PARITY OK（74 用例逐字节一致）**（探针修正版
  `_tiec_verify/p917_wip/p917_parity_fixed.tie`，见 §18.4）。

### 18.3 顺带发现（与本轮无关的既有缺陷）

* `tests/language/table_struct_elem.tie` 仍 FAIL，症状
  `irgen 未支持的表达式（tag=7，函数 main）`——struct 元素表的**字段写**
  （`t[0].y = v`）路径，与 18.1 不同族，属既有基线 FAIL，未动。
* `table<Struct>` 作**全局**变量报「行池 table<R> 全局变量 v1 暂不支持」
  （p.9.12.6 既有边界，改局部即可绕开）。
* `sgen.clone_inner`（sgen_p1.tie）的 N_CASE_BIND 特判只复制 children[0..1]
  ——多绑定解构（`case P(a, b)`）在**泛型函数克隆**下疑似截断 children[2..]
  （未实测复现，仅代码审读发现；import 合并路径已由 §18.2 修复覆盖，此疑点
  只影响泛型克隆路径）。待专项最小复现后另立条目。

### 18.4 顺带发现：跨模块全局的**限定名**访问失效（裸名可用，既有缺陷未修）

最小复现（8 行）：

    type tie<logic>
    import "compiler/interp/value.tie"
    func main() {
        var m = ivalue.new_int(42)
        ivalue.g_err → error[E00488] 未声明的变量 'ivalue'   // 读失败
        ivalue.g_ms_key = 1 → 同报错                          // 写失败
    }

* `ivalue.g_err` / `ivalue.g_ms_key =`（ns 限定全局读/写）一律 E00488
  「未声明的变量 'ivalue'」；**裸名** `g_err` / `g_ms_key =` 跨模块读写完全
  正常（value.tie 注释「模块级全局跨模块可见」的设计意图即走裸名内联）。
* 旧 exe（2fc7e125）同样复现 → 既有缺陷，非本轮回归。未修。
* parity 探针受此影响的 18 处限定名全局访问已改裸名写法
  （`p917_parity_fixed.tie`）；`map_set`「键走全局槽」契约对外部调用方实际
  只能经裸名使用，`pub` setter（如 `set_ms_key`）是更稳妥的长期形态，
  留待 language.md 全局可见性规则明确时一并定夺。

## 19. p.9.17.2 第二步：call_builtin 分派链 + interp 全树 Value 化（2026-09-28）

> 承接 §17/§18 的 vval 落地（step-1 infra），本步把**解释器热路径全树**
> 从「i64 节点 id + -1 哨兵」切换到「Value 枚举直接值」（step-2 切换）。

### 19.1 分派歧义根因：`-1` 哨兵双关失效

`Value.Nil` 是**合法 void 返回值**，旧 `-1` 哨兵双关「未命中/错误」失效；
且段内 `eval` 内建可递归重入 call_builtin，可变 handled 标志会被破坏。
修法 = **前置名单分派**：每段配无状态纯函数 `cb_is_segN(name) -> bool`
（seg1 22 名 / seg2 31 名 / seg3 8 名），分派器先判名单再进段，段尾
`return` 仅防御；错误统一经 `w_err != ""` 传播，未命中不置 w_err：

    func call_builtin(name: string, args: table<Value>) -> Value {
        if cb_is_seg1(name) { return call_builtin_seg1(name, args) }
        if cb_is_seg2(name) { return call_builtin_seg2(name, args) }
        if cb_is_seg3(name) { return call_builtin_seg3(name, args) }
        w_err = "内部错误: 未实现的内置函数 '" + name + "'"
        return Value.Nil
    }

### 19.2 全树切换账目（16 + 4 文件，探针编译零错收敛）

* interp 16 文件：`call_builtin_seg1/2/3`（82 处哨兵分类转换）、
  `interp_call_p1/p2/p3`、`interp`、`interp_p1/p2/p3`、`interp_code`、
  `interp_macro`、`interp_bin`、`interp_dbug`、`env`（整体 Value 化 +
  `table_at_call` 越界前置自检重写）、`session`（`g_ms_key` → `w_ms_key`）。
* 连带修复（value.tie 退役后 import 树失联）：`mexpand_p1` + dbug 三文件
  （crashdiag/profiler/tiedap）`g_err` → `w_err`、`ivalue.` → `vval.`。
* **lookup miss 约定迁移**：`lookup_nid`/`lookup` 改「miss 置 w_err 返回
  Nil」，调用方 `cur < 0` 判定全部改 `w_err != ""`；插值变量错误文本不同
  的两处覆盖回原文保逐字节一致。
* **合法 i64 哨兵保留**：位置/节点查找（`find_char`/`find_main` 等）、
  `parse_tokens`、`dbg_*` 系列的 `return -1` 是返回码语义，不转换
  （批量替换曾误伤 `interp_p3` 两处，编译期 E00204 暴露后回滚）。
* `env.tie` 头注释契约按行号重写；`tests/language/interp_env_file.tie` +
  `interp_env_value.tie` 全文件迁移 vval API（miss 判定改
  `type_of(vid) == W_VOID && str_len(w_err) > 0`，每个 miss 用例前置
  `w_err = ""` 防残留）。

### 19.3 RCA：has_last 收集点漏同步（9 DIFF → 修复 → 9 IDENTICAL）

A/B 初测 9 套件 DIFF，fresh 基线重建后仍 9 DIFF（真回归）。限定名探针
双跑定位：新侧 EXPR_STMT 后 `if g_has_last { last = g_lastval }` 收集点
漏同步 `has_last = true`——旧模型 `last >= 0` 兼判「有值」，Value 化后拆
`last: Value` + `has_last: bool`，**全部 10 处收集点**必须补同步
（interp.tie 2 / interp_macro 1 / interp_p1 2 / interp_p2 5），否则尾部
`vval.to_repl_string(last)` 拿 Nil 输出空串。修复脚本曾丢 `last` 行
（CRLF 正则未命中 + 三行匹配逻辑错），二次修复恢复三行结构后探针
`[3][9][6]` 与基线一致。

### 19.4 两步自举升格（旧 exe 后端不认聚合全局的绕行）

`%enum.Value` 全局 zeroinitializer 被旧 exe 后端拒（缺陷 #4b，工作树源码
已修）。绕行管线：python regex（`= global (%[\w.]+) 0$` →
`zeroinitializer`）→ `opt -O2` → `clang -fuse-ld=link -w … -Wl,/Brepro
-Wl,/STACK:134217728 -luser32 -lgdi32 -lshell32 trm_lite.a
-rtlib=compiler-rt`。Git Bash 下 `/Brepro` 被 POSIX 路径转换吞 →
`MSYS_NO_PATHCONV=1` + Windows 路径形式。

### 19.5 门禁数据

* fp 不动点：SHA256 = **ca9fa2ba…**，三哈希一致（has_last 修复后重建）。
* regress-s21：**158 PASS / 8 FAIL / 2 SKIP**，FAIL 集合逐项同基线
  （generics、proc_createprocessw_pipe、std_httpc_probe、std_net_bytes、
  std_net_text、std_sse_probe、table_struct_elem、extern_s10_ptr）。
* 11 套件 A/B：**9 IDENTICAL + 2 良性 DIFF**——DIFF 定性为旧 `-1` 哨兵
  双关缺陷被前置名单分派顺手修复（parse_int/parse_float/table_at 错误
  路径曾被「未实现的内置函数」覆盖 w_err），新输出与 golden 期望一致，
  旧侧是错的。

### 19.6 性能分账（p.9.17.2 立项目的：拆箱收益验证）

**方法**：tsh_main 宿主（内嵌 interp）双编译——OLD = 旧 tiec
（6d7664af）+ wt_head worktree 的 HEAD interp（i64 哨兵版）；
NEW = 工作树 tiec（ca9fa2ba）+ 工作树 Value interp。基准脚本各
**1,000,000 次迭代**，OLD/NEW 同轮背靠背交替 × 5 轮取中位，扣空脚本
启动基线（old 143.1ms / new 137.6ms）。外部计时（perf_counter）。

| 基准 | 循环体 | 旧净耗时 | 新净耗时 | 提速 |
| --- | --- | --- | --- | --- |
| D_loop | `i = i + 1` | 3220.5 ms | 1616.1 ms | **1.99x** |
| A_acc1 | `acc = acc + 1` + 自增 | 4864.8 ms | 2404.2 ms | **2.02x** |
| B_accv | `acc = acc + i` + 自增 | 4353.6 ms | 2310.5 ms | **1.88x** |
| E_var | `var x = i` + 累加 + 自增 | 6545.0 ms | 3974.6 ms | **1.65x** |
| C_arith | `acc = acc + i*3 - 1` + 自增 | 8038.5 ms | 3513.4 ms | **2.29x** |
| F_call | `acc = f(acc)` + 自增 | 9309.9 ms | 6201.0 ms | **1.50x** |

**读数**：拆箱全线 1.5–2.3x。算术热路径收益最大（C_arith 2.29x——
旧模型每个中间值一次 `new_node` 7 表 push，拆箱后直接值传递）；纯循环
骨架 ~2x（2.31µs 榜单基线同口径下 3.22 → 1.62µs/次）；函数调用收益
最小（1.50x——call_fn 的参数表/节点表操作占比仍高，留待第三步
value.tie 退役 + 标量池清理后另攻）。

* 测量坑备忘：①tiec 编译探针走 AOT 后端不经过 interp，测解释器必须
  经 tsh 宿主；②编译缓存键不含编译器版本，双宿主编译一律 `--no-cache`；
  ③tsh 脚本模式不支持 `unsafe extern` 声明（脚本内 clock 计时不可用，
  需外部计时）；④10 万次信号量不足（启动噪声 ±200ms），1M 迭代 +
  交替轮询才稳定。

### 19.7 遗留（第三步）

value.tie 退役文件删除、标量池槽位淘汰、内存收口；既有未修项延续
（缺陷 #3 限定名全局访问、clone_inner 多绑定截断疑点、`f_find`
interned id、`map_set` O(n²)、12 处 tests/interp 失效 import 路径）。

### 19.8 警告检查结论（-w 全量）与遗留

* 同编译器交叉对照（新 exe 编 HEAD 源 vs 编 WT 源）排除编译器因素：
  interp 闭包警告 WT 侧 +19~51 条 W00010、+17 W00005、+4 W00015，
  净减 W00016 -4、W00009 -2（总债务 25135 vs 25085，+0.2%）。
* 语法层扫描两树均**无字面空控制流块**——W00010 判定在 AST 层
  （StmtList nchild==0，位置取父语句），文件布局变化导致行列集无法
  逐条对齐归因。行为门禁全绿（fp 一致 / regress 一致 / A/B 输出一致），
  风格级波动接受，**精确归因留待警告系统支持文件名标注后清理**
  （`sm_warn_add` 仅存 line/col/msg，跨文件 import 闭包下归因成本过高，
  本轮实测已证——这是编译器警告系统的既有改进项）。

## 20. p.9.17.2 第三步：value.tie 退役 + 内存收口（2026-09-28）

### 20.1 退役账目

* `compiler/interp/value.tie`（698 行，i64 节点 id + 平行表盒装模型）删除。
  删除前盘点：全树 `import` 引用**为零**（仅 findings 文档示例与 untracked 探针
  `_p917_box.tie` 引用文本）；`ivalue.` 代码级调用残留**为零**（env/interp_call/
  interp_code/interp_macro/vval 五文件仅存注释级「语义对齐 ivalue.xxx」历史记录，
  保留不改——注释变更会触发源码字节变化连带动点重录，收益仅文档性）。
* **标量平行表槽位随文件退役**：`v_ivals`/`v_fvals`/`v_svals`（Int/Bool/Trit/Char/
  Range/Float/Str 槽）全部只在 value.tie 内部定义与使用，interp 其余文件零引用；
  vval 侧标量已内联（Value enum），无标量槽位可清——「淘汰仅服务标量的平行表槽位」
  由文件退役一并完成。
* `diagcodes.data.tie` 中 src 字段仍记 value.tie 历史路径：诊断码元数据是
  **来源记录**不是依赖，随文件保留（诊断码本体在 diagcode*.tie，不受影响）。

### 20.2 门禁（三联，独立跑全套）

* fp 不动点：SHA256 = **ca9fa2ba**，三哈希一致——与第二步**完全相同**（强预期命中：
  纯删无引用文件，driver 闭包源码字节不变，产物必然逐字节一致）。
* regress-s21：**158 PASS / 8 FAIL / 2 SKIP**，FAIL 集合逐项同基线（extern_s10_ptr /
  generics / proc_createprocessw_pipe / std_httpc_probe / std_net_bytes /
  std_net_text / std_sse_probe / table_struct_elem，全 COMPILE_FAIL 族）。
* 解释器 11 套件 A/B（旧 exe 6d7664af + wt_head interp vs 新 exe + 工作树 interp）：
  **9 IDENTICAL + 2 良性 DIFF**（interp_strings / interp_table），DIFF 内容与第二步
  门禁完全一致（旧侧「未实现的内置函数 parse_int/table_at」哨兵双关缺陷，
  新侧错误文本与 golden 一致）。

### 20.3 内存收口勘察（设计 §五假设验证）

方法：tsh 宿主（内嵌 vval interp）+ GetProcessMemoryInfo 轮询（5ms 采样 ×3 轮
取最大），PeakWorkingSet/PeakCommit 双口径。脚本组：

| 脚本 | 求值步数 | 复合值数 | peakWS | peakCommit |
| --- | --- | --- | --- | --- |
| scal_only（标量循环） | ~300 万 | 0 | 10.3 MB | **8.1 MB** |
| tbl_100k（10 万元素表） | ~20 万 | 10 万 | 15.7 MB | 14.5 MB |
| tbl_1m（100 万元素表） | ~200 万 | 100 万 | 51.9 MB | 62.0 MB |

**结论**：①标量密集求值（300 万步）内存与空脚本启动基线持平——**标量不再入池**
实证（盒装时代 v_ivals 每 Int/Bool/Trit/Char 各 push 一次，同循环池增量线性于
求值步数）；②池增长与**复合值数量**线性相关（每复合值 ~54B：24B Value 载荷 +
描述符/元素表摊销 + 尾复用共享），与求值步数无关——设计 §五的判据达成；
③**小整数预置缓存结论 = 无对象不需要**：池中只有复合值，标量零占位，
「小整数分布」不影响内存曲线（原勘察动因消失，留档备查）。

* 勘察坑：`string_builder` 等编译器侧内建在 tsh 脚本环境不存在；
  `t = table_push(t, x)` 赋值内嵌形态触发 eval_table_push 的 Void 二次写回
  （见 20.4），脚本必须**裸调用**；首轮三组数据因脚本秒退全为启动内存假数据
  ——**勘察脚本必须先验证输出正确再采数**。
* 工具留存：`_tiec_verify/bench917/memprobe.py`（可复测）。

### 20.4 顺带发现：eval_table_push 赋值内嵌 Void 二次写回（既有缺陷，未修）

`t = table_push(t, x)` 形态：eval_table_push 内部已 `isess.assign(nm, nt)` 写回
新表描述符，随后**又返回 `vval.new_void()`**，赋值语句把 RHS（Void）二次写回 t
→ 变量被 Void 污染（后续 len 报「len 只支持字符串、表或键值表」）。裸调用形态
正常（void 作为表达式语句值被丢弃）。HEAD 版（i64 哨兵）行为等价（同样
`return ivalue.new_void()`，赋值写回 -1 污染）——**既有缺陷非本轮回归**。
语义裁定待办：table_push 特判路径的返回值应为**新表值**（对齐
`t = table_push(t, x)` 的 Rust 语义）或赋值侧识别 void 不写回；因涉及
exec_stmt_assign 与特判路径的职责边界（§9.17.3 直驱改造相邻），另立条目处理。

### 20.5 状态

p.9.17.2 三步全部落地（基建 → 热路径切换 → 清理与内存收口）。p.9.18.1 面 A
侧附加交付（嵌入裁剪形态 + 内存峰值/稳态报告）随 p.9.18.5 验收；本节内存勘察
数据可作为其基线引用。既有未修项延续：缺陷 #3 限定名全局访问、clone_inner
多绑定截断疑点、`f_find` interned id、`map_set` O(n²)、12 处 tests/interp 失效
import 路径、20.4 赋值内嵌写回语义。

## 21. p.9.17.3 后半：call_fn 入口全面 nid 化（2026-09-28）

> 承接 §17（变量环境 interned id），本批把**函数调用路径**的字符串查找全部
> 整数化：函数表（f_find）、宏表（m_has）、extern 表（e_has）、内置名单
> （is_builtin + cb_is_seg1/2/3）。

### 21.1 改动账目

* **session.tie**：f/m/e 三表各加 `*_nids` 平行表（interned id 键），
  `f_find_nid/f_put_nid/f_get_nid/f_has_nid/m_put_nid/m_has_nid/e_add_nid/
  e_has_nid` 主实现；字符串版全部转薄包装（intern 一次转调，冷路径）。
  f_keys/m_keys/e_keys 字符串表保留（显示/调试，与 nid 表下标对齐）。
* **interp_call_p1.tie**：`call_fn_nid(nid, args, arg_nodes)` 主实现
  （`call_fn` 转薄包装）；`is_builtin_nid` 名单 nid 化。
* **interp_call_p2.tie**：`call_builtin_nid` 分派（判段用 nid，段函数仍收
  name 文本——段内个别内建要用名字，lookup 还原一次）；cb_is_segN 转薄包装。
* **interp_p3.tie**：gen_call 热入口直传 nid（`nname_str` 构造延迟到冷分支）；
  table_push 特判改惰性 nid 比较；gen_method_call 尾部 intern(full) 一次。

### 21.2 RCA：辅助函数取名单 = 每次判定多付一次完整解释器调用

首版实现把内置名单抽成 `bi_names()` 辅助函数（is_builtin_nid 每次调用取表）
——**该辅助函数本身是被解释执行的 tie 代码**，每次判定多付一次完整解释器
函数调用。F_call 交替 A/B 实测 **+28%**（5175→6643ms/百万次）。二分定位：
短路 builtin 判定后 F_call 恢复（Fpure 1M：s4c 4640 vs s4b 6341 vs prev 4831ms）
→ 62 项名单扫描 + 辅助调用合计 1.7µs/次。修复 = 名单**内联惰性构建**在
nid 函数体内（字符串版转薄包装，单一数据源零漂移）。

### 21.3 RCA：运行时数组线性扫描 vs 编译期 if 链的 9 倍差距

内联修复后仍 +31%？二分实验（Fpure 纯用户函数调用脚本）：**62 项运行时
数组线性扫描 = 1.70µs/次**（数组边界检查 + 动态加载 ~27ns/项），而原版
62 项**编译期展开的字符串 if 链**仅 0.19µs/次（立即数长度比较 + 短跳转，
分支预测完美）——**差 9 倍**。修复 = 名单构建后**插入排序 + 查询二分**
（62 项 → 6 次比较 ≈ 0.16µs）。cb 三段（22/31/8 项）同改。

* 教训沉淀：解释器自身代码里，**「编译期展开的常量 if 链」是地基性能**；
  把它改成「运行时数组扫描」哪怕键从字符串换成语义更优的整数，也敌不过
  逐项数组访问开销——名单类查找的终态是**排序 + 二分**（或哈希，待 tie
  原生 map 成熟）。
* 教训沉淀：**热路径辅助函数调用 = 整个解释器调用开销**。名单/常量表的
  惰性构建必须**内联在热函数体内**（ready 标志守卫），不得经任何 tie 函数
  中转。

### 21.4 性能分账（交替 8 轮，中位与最小一致）

系统噪声本轮偏高（±5%，同 exe 两轮 F_call 波动 18% 实测在案），8 轮中位与
最小值双重对比方向一致：**F_call −2.2%、Fpure −2.1%**（s4d vs prev）。
二分前的 +28~31% 恶化完全消除。收益较 §17 变量环境批次（−4~8%）小：
原版 is_builtin if 链本就快（0.19µs），本轮主要收益是**结构统一**——
调用路径全部 nid 化（变量/函数/宏/extern/内置名单同一套整数键范式），
为 p.9.17.4 JIT 的冷热边界（nid 即符号）铺路。

### 21.5 门禁

* fp 不动点：SHA256 = **a0d7f018**，三哈希一致（源码字节变化 → 新动点，
  tiec.exe 已升格）。
* regress-s21：**158 PASS / 8 FAIL / 2 SKIP**，FAIL 集合逐项同基线。
* 解释器 11 套件 A/B：**9 IDENTICAL + 2 良性 DIFF**（同 §19/§20 基线）。
* 冒烟：内置调用 / 用户函数 / 命名空间互调 / table_push 特判 / 字符串内建
  全通过（tsh 宿主脚本）。
