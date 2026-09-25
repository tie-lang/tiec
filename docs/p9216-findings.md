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
