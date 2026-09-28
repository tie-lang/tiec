## 第 1 章  词法与记号

| 节 | 条目（规范要求） | 状态 | 证据 | 备注 |
| --- | --- | --- | --- | --- |
| 1.1 | 头部三种形式：`type tie` / `type tie<logic>` / `type tie<db: vector, unsafe>` | 已实现 | A: `--prep-only s1_1a.tie`→「识别为 type 文件」；`s1_1b.tie`→logic；`s1_1c.tie`→db | 裸形式落到 `type` 角色（B: role_reg.tie:44 `reg_base("type","lib","")`） |
| 1.1 | 头部必须最前、连续（其间允许空行） | 已实现 | A: `s1_1d.tie`（前导注释 + 头部 + 空行）识别为 logic；`s1_1g.tie`（语句后另起 `type tie<logic>`）E00000「实际是 标识符 'type'」 | — |
| 1.1 | 未声明头部按 logic 处理 | 已实现 | A: `s1_1f.tie`（无头部）识别为 logic | — |
| 1.1 | 文件名与头部声明不一致 → 以头部为准并给警告 | 部分实现 | A: `s1_1e.script.tie`（头 `type tie<logic>`）报 `error[E00000] 文件名与头部角色声明不一致；基础角色不一致: 文件名 'script' vs 头部 'logic'`；B: driver.tie:347 `render_error` | **规范与实现冲突**：规范要求「警告」，实现是硬错误（`编译错误`，R3 单一真相原则） |
| 1.2 | 12 种角色均被识别 | 已实现 | A: `--prep-only s1_2_<role>.tie` 12 个全部输出对应角色名；B: role_reg.tie:41-53 | 实现另有规范未列的 `type`/`tieir` 两个基础角色 |
| 1.2 | logic → 可执行程序 | 已实现 | A: `o_logic.exe` 编译成功 | — |
| 1.2 | class → 只编译静态库、不产生入口 | 已实现 | A: `o_class.exe` 输出「库编译成功」；B: role_reg.tie:43 output=lib | — |
| 1.2 | script → 顶层语句按顺序直接执行、不要求入口 | 未实现 | A: `s1_2_script_tl.tie`（`println(42)` 顶层）报 E00000「顶层只允许函数定义…实际是 标识符 'println'」，与 logic 完全相同 | 角色被登记（B: role_reg.tie:42 output=exe），但解析策略与 logic 无差别 |
| 1.2 | data → 只允许数据声明与字面量，不允许函数体 | 部分实现 | A: `s1_2_data_fn.tie`（含 `func f()`）仅提示「已转交数据工具链」，不报错；B: role_reg.tie:48 data=pass | 未实施「不允许函数体」约束；实际是 pass 角色 |
| 1.2 | ui → 编译器生成界面代码 | 未实现 | A: 「已转交 UI 工具链 —— v0.1 UI 工具链尚未实现」；B: role_reg.tie:49 ui=pass | — |
| 1.2 | db → 生成建表与读写代码 | 未实现 | A: 「v0.1 数据库工具链尚未实现」；B: role_reg.tie:50 db=pass | 头部参数 `vector` 被接受（见 1.1c）但无消费者 |
| 1.2 | port → 声明对外契约 | 未实现 | A: 「v0.1 端口工具链尚未实现」；B: role_reg.tie:51 port=pass | — |
| 1.2 | ir → 直接产出中间代码 | 已实现 | A: `o_ir.exe` → 「已生成 LLVM IR: o_ir.ll」；B: role_reg.tie:45 ir=check | — |
| 1.2 | test → 只做检查与执行，不产出交付物 | 部分实现 | A: 产出 `o_test.exe`（与 logic 相同）；B: role_reg.tie:46 test output="" | 与 logic 无差别；注释称 test/bench 为「角色发现目录」 |
| 1.2 | bench → 用于性能测量 | 部分实现 | A: 产出 `o_bench.exe`；B: role_reg.tie:47 | 未见基准专属产能 |
| 1.2 | zd → 结构化二进制数据文件 | 部分实现 | A: 「zd 压缩数据文件…用 tiedb compact/decompress 处理」；B: role_reg.tie:52 zd=pass | 编译侧不生成产物，转外部工具 |
| 1.2 | tsh → 由终端脚本宿主执行 | 部分实现 | A: 「由 tshell 运行: tshell\src\tsh_main.exe -f …」 | 编译侧不生成产物 |
| 1.2 | 修饰 unsafe：整文件不安全上下文 | 已实现 | A: `m_unsafe.tie`（`type tie<logic, unsafe>` + 直接 `deref(int_to_ptr(0))`）编译通过并输出 0；对照 `m_plain.tie` 报 `E00586 必须在 unsafe 块或 unsafe 函数中`；B: driver.tie:355 | — |
| 1.2 | 修饰 owned | 部分实现 | B: role_reg.tie:57 `reg_mod("owned")` | 仅登记，全仓无消费者（grep 无 `"owned"` 行为分支） |
| 1.2 | 修饰 embedded | 部分实现 | B: role_reg.tie:58 `reg_mod("embedded")` | 仅登记，全仓无消费者 |
| 1.2 | 角色集开放，项目可声明自定义角色 | 已实现 | B: role_reg.tie:63-133 `register_role_map`（含 kind/params/output 白名单与拦截） | — |
| 1.3 | UTF-8 + 码点/字节双尺度 `str_len`/`len`/`str_char` | 已实现 | A: `s1_3.exe` 输出 `2`/`6`/`你` | — |
| 1.4 | 行注释 `//`、块注释 `/* */` | 已实现 | A: `s1_4.tie` 编译运行输出 3 | — |
| 1.4 | `///` 文档注释附着到紧随声明 | 已实现 | A: `--dump-docs s1_4b.tie` → 「共 2 条声明 doc: [3] add / [7] main」；B: lex_scan.tie:605 `scan_doc_line` | `--dump-docs` 对**含头部**文件报 E00000（早于头部剥离），见 ROAD.md:363 已有同结论补充 |
| 1.4 | 函数体内的 `///` 退化为普通注释 | 已实现 | A: `--dump-docs s1_4c.tie` → 仅 1 条（main），体内注释未登记 | — |
| 1.5 | Unicode 标识符可用 | 已实现 | A: `s1_5.tie`（`var 用户数`、`结果1`）输出 4 | — |
| 1.5 | 类型名大写 / 函数变量小写的约定（非强制） | 非规范条目 | — | 规范自述「约定而非强制，编译器不做检查」，无可编译特性 |
| 1.6 | 关键字表封闭 | 部分实现 | A/B: `lex_symtab.tie:36` `build_kw()` 69 项；规范 §1.6 去重后 70 项（集合比对见备注） | 规范有实现无：`run`/`self`/`type`；实现有规范无：`extends`/`with`（详见下两行） |
| 1.6 | `run`/`self`/`type` 为保留字 | 未实现 | A: `s1_6_run/self/type.tie`（`var run = 1` 等）均编译成功 → 三者为普通标识符；B: `run`=位置识别 pexpr_p2.tie:127、`self`=pstmt_top_p3.tie:117,328、`type`=role_reg.tie:44 | 规范把三者列进「关键字…用作标识符即报错」的表，实测不报错 |
| 1.6 | 规范表未列 `extends`/`with` | 已实现 | A: `s1_6_extends.tie`、`s1_6_with.tie`（`var extends = 1`）均报 `E00485 期望标识符，实际是 Extends/Token98` → 是保留字 | 属**规范 §1.6 表遗漏**（§1.12 表与 §6.5 正文确有 `with`/`extends`） |
| 1.7 | 十进制/十六进制/二进制/八进制/下划线分组 | 已实现 | A: `n1`..`n5` 全部编译成功；`s1_7_val.exe` 输出 255/11/493/1000000/51966；`0x_FF`→255 | — |
| 1.7 | 浮点 `3.14` / `1.5e3` | 已实现 | A: `n6`/`n7` 编译成功；`s1_7_val.exe` 输出 3.1400000000000001 | — |
| 1.7 | 类型后缀 `42i32` / `0x80u16` | 已实现 | A: `n8`/`n9` 编译成功；B: lex_scan.tie:506-509 后缀白名单 | — |
| 1.7 | f32 字面量 `1.2f32`（带类型后缀） | 部分实现 | A: `m2`（`var v: f32 = 1.2f32`）报 `error[E00000] 中间优化失败…%1 = fadd float 1.2, 0.0` | 后缀被词法接受；坏在**f32 浮点常量发射**：`var v: f32 = 1.2`（无后缀）同样失败，而 1.5/2.5/3.0（二进制可精确表示）通过 → 与后缀无关的通用后端缺陷 |
| 1.7 | 平衡三进制 `0t1T0` | 未实现 | A: `t9`（`0t1T0`）报 `E00000 @4:22 期望 语句结束符，实际是 标识符 'T0'`（词法切成 `0t1` + `T0`） | **规范自身矛盾**：散文写「数字只用 0/1/2」，示例却用 `T`。实现只支持 0/1/2（`0t12`=5、`0t120`=15，纯三进制而非平衡式） |
| 1.7 | 三值字面量 `-1t` / `0t` / `1t` | 已实现 | A: `t1`/`t2`/`t3` 通过；`1T`（t8）亦通过；`2t`/`3t` 报 `E00001 trit 字面量越界`；B: lex_scan.tie:513-533 | — |
| 1.8 | `true`/`false` 布尔字面量 | 已实现 | A: `s1_12_cmp.exe`、`s1_8` 系列编译运行 | — |
| 1.8 | `trit` 字面量复用 `true`/`zero`/`false` | 已实现 | A: `t10`/`t11`/`t12`（`var v: trit = true/zero/false`）均编译成功 | — |
| 1.9 | 普通字符串 `"..."` | 已实现 | A: `s1_9_plain.tie` 编译运行 | 但其插值行为与规范冲突，见下行 |
| 1.9 | 原始字符串 `r"..."`（无转义、无插值） | 已实现 | A: `s1_9_raw.exe` 输出 `C:\path\to\file`，`str_len`=15；B: lex_scan.tie:329 `scan_raw_string` | — |
| 1.9 | 多行字符串 `"""..."""`（缩进剥离） | 已实现 | A: `s1_9_triple.exe` 输出 line1/line2；B: lex_scan.tie:155 `scan_triple_string` | — |
| 1.9 | 插值字符串 `h"...{e}..."` | 未实现 | A: `s1_9.tie` 的 `h"共 {n} 项"` 报 `E00000 @8:19 期望 语句结束符，实际是 字符串`；B: lex_scan.tie:544-558 `scan_ident` 只特判 `lex == "r"`，无 `h` 分支 | **规范领先于实现**：h 前缀是本次规范新增要求，实现未跟上 |
| 1.9 | 不带 h 的字符串花括号即字面量 | 未实现 | A: `s1_9_plain.exe` 的 `"共 {n} 项"` 输出 `共 3 项`（发生插值）；B: lex_scan.tie:74-125 `{` 前瞻触发插值；ROAD.md:133 p.8.2.3 | **规范与实现冲突**：实现默认插值（`"Hello, {name}"`），规范要求必须 `h` 前缀才插值 |
| 1.10 | 自动分号插入（行尾运算符续行、显式分号混用） | 已实现 | A: `s1_10.exe` 输出 36/3 | — |
| 1.11 | 行续行（行尾反斜杠） | 已实现 | A: `s1_11.exe` 输出 6 | — |
| 1.12 | 算术 `+ - * / %` | 已实现 | A: `s1_12_arith.exe` 输出 10/4/21/2/1 | — |
| 1.12 | 整除 `\` 与成对取余 `%%` | 已实现 | A: `s1_12_div.exe` 输出 2/1；B: pexpr_p1.tie:396 `B_IDIV`、:393 `B_FLOORMOD` | — |
| 1.12 | 幂 `**` / 带检查幂 `**?` | 已实现 | A: `s1_12_arith.exe` 输出 1024/1024 | — |
| 1.12 | 带检查 `+? -? *?` | 已实现 | A: `s1_12_div.exe` 输出 11/-1/30 | — |
| 1.12 | 比较（含链式）`== != < > <= >=` | 已实现 | A: `s1_12_cmp.exe` 输出 `cmp ok`/`chain ok`/`chain2 ok`（`1 < 2 < 3` 可用） | — |
| 1.12 | 逻辑 `&& \|\| !` | 已实现 | A: `s1_12_cmp.exe`/`s1_12_bit.exe` | — |
| 1.12 | 位运算 `& \| ^ << >>` | 已实现 | A: `s1_12_bit.exe` 输出 2/7/5/16/8 | — |
| 1.12 | 位取反 `~` | 未实现 | A: `s1_12_not.tie` 报 `E00481 无法识别的字符 '~'`；B: lex_symtab.tie:99 `build_sym()` 60 项无 `~` | 记号层即不存在 |
| 1.12 | 赋值与复合赋值 `= += -= *= /= %=` | 已实现 | A: `s1_12_bit.exe` 输出 3（链式 `+=1;-=2;*=3;/=2;%=5`） | — |
| 1.12 | 其余复合赋值 `\= &= \|= ^= <<= >>=` | 已实现 | A: `s1_12_ideveq.exe` 输出 2（`\=`）；`s1_12_bit.exe` 输出 6（&=/\|=/^=/<<=/>>=） | — |
| 1.12 | `->` 管道/返回位/短闭包/分支臂 | 已实现 | A: `dataflow_arrow.exe` 7 项全 PASS；`s2_6f` `->` 返回位；B: pexpr_p2.tie 链式管道 | — |
| 1.12 | `<-` 反向赋值/反向解构 | 已实现 | A: `s1_12_larrow.exe` 输出 5/15（`x <- 5` 与 `(a,b) <- t`）；`dataflow_arrow.exe` `PASS assign_both/assign_field/assign_index` | — |
| 1.12 | `in` / `not in` | 已实现 | A: `s1_12_in.exe` 输出 `in ok`/`notin ok`；B: pexpr_p5.tie:61-62 | — |
| 1.12 | `?:` 安全默认值 | 已实现 | A: `s1_12_opt.exe` 输出 `42 -1 hi def 20 -1 -1 5 -1 100 7 -1`；负例 `s1_12_optneg.tie` 报 `E00100` | — |
| 1.12 | `?` 存在判定 / `?[` 安全索引 | 已实现 | A: `s1_12_opt.exe`（`t1?[1]`=20、`g?[1]?[2]`=5、越界/None→-1） | — |
| 1.12 | `?.` 可空链字段访问 | 部分实现 | A: `s1_12_safeaccess.tie` 报 `E00365 变体 'Some' 的 payload 暂不支持类型 'P'` | **缺一半**：语法/推导存在（B: sinfer_ie_ie2.tie:353/385，要求载荷为 struct），但唯一适用载荷 struct 被 enum payload 白名单排除 → 实际不可用 |
| 1.12 | `\` 解引用（不安全上下文） | 未实现 | A: `s1_12_deref.tie`（`var v = \p`）报 `E00000 @6:17 无法以 Token108 开始表达式`；B: pexpr_p1.tie:396 `\` 仅映射 `B_IDIV` | 解引用实为内建 `deref()`/`deref_write()`（tests/asym_probe），非运算符 |
| 1.12 | 范围 `..`（左闭右开） | 已实现 | A: `s1_12_in.exe`（`for i in 0..3`）求和 3 | — |
| 1.12 | 范围 `..=`（左闭右闭） | 未实现 | A: `s1_12_rangeincl.tie`（`0..=3`）报 `E00000 @5:17 无法以 Eq 开始表达式`；B: lex_symtab.tie:99 无 `..=` | 词法切成 `..` + `=` |
| 1.12 | `...` 变长形参/实参展开 | 已实现 | A: `variadic.exe` 输出 6/0/5/5/4；`spread_call.exe` 输出 `5,6,1,2,3,100` 等 | — |
| 1.12 | `@` 元素标记与注解 | 已实现 | A: `annot.exe` → 「annot 探针全过」；B: lex_tokdefs.tie:104 | — |
| 1.12 | `#` 属性与标签 | 已实现 | A: `s1_12_attr.exe`（`#[unsafe.share]`）输出 `tagged_fn: 42`；B: lex_tokdefs.tie:91 | — |
| 1.12 | `$` 宏插值 / 准引用 `` ` `` | 已实现 | A: `macro_hygiene.exe` 输出 `dbl=42/mixed=16/bump=6/bump=8/caller __r=99`（`macro fldbl(x: code) -> code { return \`( ($x) * 2 ) }`） | — |
| 1.12 | `with` 不可变更新 | 已实现 | A: `table_with.exe` → 5 项全 PASS | — |
| 1.12 | 图的边与节点操作 `-\| <-\| ->x ~x -><` | 未实现 | A: `g1.tie`（`1 -\|\ 2`）报 `E00000 无法以 Pipe 开始表达式`；`g3.tie`（`1 ->x 2`）报 `E00000 期望语句结束符，实际是 整数 2`；`s1_12_not.tie` 报 `E00481 '~'`；B: lex_symtab.tie:99 无任一记号；ROAD.md:419 自述「运算符形态留作后续语言档」 | 图能力以 tlib `std/dataflow.tie` 库形式存在（无语言算子） |
| 1.13 | 12 项上下文关键字均不报错（可作标识符） | 已实现 | A: `s1_13_ident.exe` 用 `fn/let/not/try/defer/guard/out/inout/target/array/r/h` 全作变量名编译通过，输出 78 | — |
| 1.13 | `fn` 函数类型位置 | 已实现 | A: `s2_14.exe`（`fn(i64) -> i64`） | — |
| 1.13 | `let` 条件解构位置 | 已实现 | A: `if_let.exe` 输出 42/none2/many42/7 | — |
| 1.13 | `not` 与 `in` 组合 | 已实现 | A: `s1_12_in.exe` 输出 `notin ok` | — |
| 1.13 | `try` 错误聚合块 | 已实现 | A: `try_block.exe` 输出 ok:1/err:div0/some:15/none-at | — |
| 1.13 | `defer` 作用域收尾块 | 已实现 | A: `defer_stmt.exe` 输出 --order--/1/2/C | — |
| 1.13 | `guard` 前置条件 | 已实现 | A: `guard_early.exe` 输出 pos/zero/neg/small:1 | — |
| 1.13 | `run` 建立并发执行体 | 已实现 | B: pexpr_p2.tie:127-130（`run` 后跟标识符时识别）；A: tests/m6_actor `run Logger()` 用例编译运行 | — |
| 1.13 | `self` 接收者位置 | 已实现 | B: pstmt_top_p3.tie:117,328（形参名为 `self` 时构造 `N_NAMED_TYPE`）；A: `interface_trait.exe` 中 `self` 形参 | — |
| 1.13 | `out / inout / target` 内联汇编操作数位置 | 已实现 | A: `asm_target_probe.exe` → `PASS batch6-asm-target`；B: pexpr_p3.tie:43-47 | — |
| 1.13 | `array` 定长数组类型位置 | 已实现 | A: `array_probe.exe` 输出 len(a)=8/…/s2sum=6 | — |
| 1.13 | `r` 紧跟引号＝原始字符串 | 已实现 | A: `s1_9_raw.exe`；B: lex_scan.tie:554-557 | — |
| 1.13 | `h` 紧跟引号＝插值字符串 | 未实现 | A: 同 1.9（E00000） | — |

> 本章：已实现 58 / 部分实现 11 / 未实现 13 / 非规范条目 1

## 第 2 章  类型系统

| 节 | 条目（规范要求） | 状态 | 证据 | 备注 |
| --- | --- | --- | --- | --- |
| 2.1 | 有符号整数 `i8 i16 i32 i64` | 已实现 | A: `s2_1.exe` 编译运行输出 23 | — |
| 2.1 | 无符号整数 `u8 u16 u32 u64` | 已实现 | A: `s2_1.exe` | — |
| 2.1 | 128 位整数 `i128 u128` | 已实现 | A: `s2_1.exe`（`var i: i128 = 9; var j: u128 = 10`）输出 23；B: lex_symtab.tie:38 | — |
| 2.1 | 浮点 `f64` | 已实现 | A: `s2_1.exe`（`var l: f64 = 2.5`） | — |
| 2.1 | 浮点 `f32` | 部分实现 | A: `m6/m7/m8`（1.5/3.0/2.5）通过；`m1/m2`（1.2）报 opt 失败 `fadd float 1.2` | 非二进制精确表示的 f32 字面量触发后端常量发射缺陷 |
| 2.1 | `bool` | 已实现 | A: `s1_12_cmp.exe` | — |
| 2.1 | `trit` | 已实现 | A: `s2_2.exe` 输出 0/1/-1/0/6 | — |
| 2.1 | `char` | 已实现 | A: `s1_9.tie`（`var c: char = 'A'`）；`table_any_elem.exe` 的 `case char` | — |
| 2.1 | `string` | 已实现 | A: `s1_3.exe` | — |
| 2.1 | `void`（仅作返回类型） | 已实现 | A: `s2_1_void.exe`（`func f() -> void`）输出 v/1 | — |
| 2.1 | `code`（编译期代码片段） | 已实现 | A: `macro_hygiene.exe`（`macro fldbl(x: code) -> code`） | — |
| 2.2 | `trit` 三值类型与正/零/负取值 | 已实现 | A: `s2_2.exe`；`t10-t12` | — |
| 2.2 | 三值逻辑：与取小、或取大、非取反 | 已实现 | A: 解释器 `interp_trit.tie`（Kleene 真值表）；原生后端 `s2_2.exe` 输出 `true&&zero`=0、`true||false`=1、`!true`=-1、`!zero`=0 | — |
| 2.2 | 混合 trit 与整数按提升规则转为整数 | 已实现 | A: `s2_2_mix.exe`（`var x = a + m`，a:trit=m+1、m:i64=5）输出 6 | — |
| 2.2 | 除法与取余对 trit 不开放 | 部分实现 | A: `s2_2_div.tie`（`a / b`，a/b 均 trit）报 `IR 生成失败: irgen 未支持的表达式（tag=9）` | 被拒绝，但发生在**代码生成期**而非语义检查期（sinfer 放行）→ 缺「语义期报错」这一半 |
| 2.3 | 宽类型关键词 `num` / `text` / `misc` 可用作标注 | 已实现 | A: `w_a`(num=42)/`w_b`(num=3.14)/`w_s`(text="hi")/`w_c`(text='x')/`w_d`(misc=true)/`w_e`(misc=3)/`w_f`(num=7i32) 全部编译成功 | — |
| 2.3 | 宽类型「只存在于编译期，变量参与运算时用推导出的具体类型」 | 未实现 | A: `w_t5`（`num + 1`）报 `E00270 二元运算两侧类型不一致；num 与 i64`；`w_t6`（`text + string`）报 `E00270 text 与 string`；`w_t7`（`misc` 作 if 条件）报 `E00165 if 条件必须是 bool`；`w_t3`（`to_string(num)`）opt 失败 `sext ptr … to i64` | 实现把宽类型当**独立类型**，不做编译期落型：声明可过、任何使用皆错（与规范示例 `var a: num = 42 // 推导为 i64` 不符） |
| 2.4 | 表字面量 `table<T>` / 动态表构造器 / `table_push` | 已实现 | A: `s2_4.exe` 输出 3/3/10 | — |
| 2.4 | 表可嵌套、`for-in` 遍历、`len` | 已实现 | A: `s2_4.exe`（`table<table<i64>>` + 双层 for-in）输出 10 | — |
| 2.5 | 映射字面量 `map<V>` / 下标读写 | 已实现 | A: `s2_5b.exe`（`["alice":3,…]`、`age["carol"]=7`）输出 3/5 | — |
| 2.5 | 键为字符串时可用点号访问值 | 已实现 | A: `s2_5b.exe`（`age.bob`）输出 5 | — |
| 2.5 | `age.has("alice")` 成员判定 | 未实现 | A: `s2_5.tie` 报 `E00475 方法调用的对象必须是 struct/enum 实例或 struct/enum 名，实际是 map<i64>` | 成员判定须改用 `in`（实测可用） |
| 2.6 | 元组类型 `(T1, T2)` 作返回类型 | 已实现 | A: `sugar_set.exe`（`func divmod(...) -> (i64, i64)`）输出正常；`s2_6f.exe` | — |
| 2.6 | 元组命名分量 `(lo: i64, hi: i64)` 与按名访问 | 已实现 | A: `s2_6d.exe`（`t.lo`=1、`t.hi`=9）；B: pexpr_type.tie:261 | — |
| 2.6 | 元组解构赋值 | 已实现 | A: `s2_6f.exe`（`var (lo, hi) = mm()`）输出 10；`sugar_set.exe` 的 `for (k,v) in pairs` | — |
| 2.6 | 规范示例 `return 1, 9` 与 `var lo, hi = …` | 未实现 | A: `s2_6b.tie`（`return 1, 9`）报 `E00000 @4:13 期望语句结束符，实际是 Comma`；`s2_6e.tie`（`var lo, hi = mm()`）报 `E00484 期望 '='，实际是 Comma` | **规范示例语法与实现不一致**（实现要求 `return (1, 9)` / `var (lo, hi) = …`）；特性本身可用 |
| 2.7 | 显式类型标注与省略推导 | 已实现 | A: `s2_1.exe`、`s2_4.exe`（`var dyn = table_new_i64()`） | — |
| 2.8 | 泛型函数 `<T>` | 已实现 | A: `s2_8.exe`（`max_of<T>`）输出 7 | — |
| 2.8 | 泛型结构 `struct Box<T>` | 已实现 | A: `s2_8.exe`（`Box<i64>(9)`）输出 9；`v3.exe` | — |
| 2.8 | 类型参数约束 `<T: Drawable>` | 已实现 | A: `interface_trait.exe` 输出 27/circle/12/rect/25/shape（`area_of<T: Drawable>` 静态分派）；B: interface 关键字 lex_tokdefs.tie:106 | 约束违规有诊断（接口第一参须 self / 未 pub 等） |
| 2.9 | 枚举 + 无名 payload + switch 分支匹配 | 已实现 | A: `s2_9b.exe`（`enum Shape { Circle(f64) Rect(f64,f64) }`）输出 3.14159…/6 | — |
| 2.9 | 命名 payload `Circle(r: f64)` | 未实现 | A: `s2_9.tie`（`Circle(r: f64)`）报 `E00484 @4:13 期望 ')'，实际是 Colon` | **规范示例语法与实现不一致**（实现为无名 payload） |
| 2.9 | enum payload 可为 struct / fn | 未实现 | A: `s2_9_struct.tie`（`enum E { A(P) }`）报 `E00365 变体 'A' 的 payload 暂不支持类型 'P'`；B: scollect_port_q1.tie:322-334 白名单仅 int/bool/char/trit/string/f64/table/map | 与 ROAD.md:121 p.8.1.8 `[ ]` 一致（记录属实） |
| 2.10 | `any` 容纳异质数据、显式取用 | 已实现 | A: `table_any_elem.exe` 7 项全 PASS（`as_i64`/`as_f64`/`as_string`/`as_bool` 拆箱 + `switch x { case i64: … }` 类型分派 + `table<any>` 异构表） | — |
| 2.10 | `is_num(v)` 类型判定（规范示例） | 未实现 | A: `s2_10.tie` 报 `E00489 未定义的函数 'is_num'` | 规范示例谓词名不存在；实现以 `as_*` + `switch 类型` 承担 |
| 2.11 | 数值类型显式转换（窄化/整数→浮点/→文本） | 部分实现 | A: `s2_11c.exe`（`as_i32`/`as_f64`）输出 1000/1000；`s2_11.tie`（`to_i32`）报 `E00489`、`s2_11b.tie`（`to_f64`）报 `E00489`；`to_string` 可用 | **命名不一致**：规范写 `to_i32/to_f64`，实现为 `as_i32/as_f64`。功能在，名字不同 |
| 2.11 | 指针↔整数转换仅在 unsafe 允许 | 已实现 | A: `m_plain.tie` 报 `E00586 调用 unsafe 内置 'int_to_ptr' 必须在 unsafe 块或 unsafe 函数中`；`m_unsafe.tie` 通过 | — |
| 2.12 | `ptr<T>` 裸指针 | 已实现 | A: `x_unsafe_full.exe`（`unsafe fn ptr_walk(base: ptr<i64>, n: i64)`）输出 99/not-null/99 | — |
| 2.12 | `slice<T>` 切片 | 已实现 | A: `x_slice_table_probe.exe` 输出 3/20/30；B: 元素类型桥 at_f64 | — |
| 2.12 | `atomic<T>` 原子类型 | 已实现 | A: `x_atomic_asm.exe`（`var c: atomic<i64> = 0`）输出 10/15/cas-ok | — |
| 2.12 | `guard<域>` 凭据 | 已实现 | A: `x_actor_a5_guard.exe` 输出 get:1/use:2/with:3（`guard<share>` + `unsafe.get/use`） | — |
| 2.13 | `array<T, N>` 类型 + `array_init` | 已实现 | A: `s2_13.exe` 输出 0/3；`array_probe.exe` | — |
| 2.13 | 长度不同即不同类型 | 已实现 | A: `s2_13_c.tie`（`array<f64,4> = array<f64,3>`）报 `E00377 变量 'b' 类型不匹配；标注 array<f64, 4>；表达式推导为 array<f64, 3>` | — |
| 2.13 | 常量下标越界在编译期发现 | 已实现 | A: `s2_13_b.tie`（`v[5]`，长度 3）报 `E00000 数组下标越界；索引 5 ≥ 长度 3` | — |
| 2.13 | 嵌套定长数组 | 已实现 | A: `s2_13.exe`（`array<array<f64,3>,3> = array_init(v)`）、`v5.exe` | — |
| 2.14 | 函数类型 `fn(A, B) -> R` 作变量/形参 | 已实现 | A: `s2_14.exe`（`var cb: fn(i64) -> i64 = double`、`apply(g: fn(i64)->i64, v)`）输出 42/10；B: ROAD.md:347 p.9.11.17 | — |
| 2.15 | 行池 `table<Struct>`：按标识稀疏寻址、默认行、`len`=最大标识+1 | 已实现 | A: `s2_15.exe`（rowpool_probe）→ `_p9126_rowpool_probe ALL PASS`（写读回环/稀疏大 id/零行/多字段/复写/越界读默认行）；B: ROAD.md:388 p.9.12.6 | 边界（返回值/形参/全局行池/table_push 拒绝）有 companion 负例 |
| 2.16 | 十进制 `d` 后缀字面量（精确十进制） | 未实现 | A: `s2_16.tie`（`0.1d + 0.2d`）报 `E00000 @4:20 期望语句结束符，实际是 标识符 'd'`；B: lex_scan.tie:506-513 后缀白名单无 `d` | **规范领先于实现**：规范 §2.16 给了完整写法，实现完全没有 |
| 2.16 | 大整数 `big_parse` | 未实现 | A: `s2_16b.tie` 报 `E00489 未定义的函数 'big_parse'` | 与 ROAD.md:314 p.9.10.11 `[ ]` 一致 |
| 2.16 | 除法显式精度 `div_ctx(a,b,10,half_even)` | 未实现 | B: 全仓（compiler + tlib）grep 无 `div_ctx`/`half_even` 任何定义或调用 | — |
| 2.17 | `alias` 类型别名（透明） | 已实现 | A: `s2_17.exe`（`alias Matrix`、`alias Pair<T> = (T,T)`、`alias Handler = fn(i64)->i64`）输出 2/7/10；B: ROAD.md:366 p.9.11.32 | — |
| 2.18 | 值参数：解析与实例化 | 部分实现 | A: `v2.tie`（`func zeros<N: i64>() -> array<f64, N>` + `zeros<3>()`）解析成功、实例化名 `zeros$n3`，但报 `IR 生成失败: irgen 未支持的表达式（tag=7，函数 zeros$n3）` | 前端可解析/实例化，后端未落地 |
| 2.18 | 值参数作数组长度（规范三例核心） | 未实现 | A: `v12.tie`（`struct Buffer<CAP: i64> { var data: array<u8, CAP> = array_init(0) }`）报 `IR 生成失败（tag=7）`；`v6.tie`（无初值）解析期报 `E00000 期望字段声明结束符，实际是 RBrace` | 与 ROAD.md:361 p.9.11.27 `[ ]` 一致；另发现 struct 的 array 字段本身不支持（`v8/v9/v10`） |
| 2.18 | 值参数默认值 `<CAP: i64 = 1280>` 与作字段初值 | 已实现 | A: `v13.exe`（`struct Cfg<CAP: i64 = 1280> { var cap: i64 = CAP }` + `Cfg<512>()`）输出 512 | — |

> 本章：已实现 40 / 部分实现 4 / 未实现 10 / 非规范条目 0

## 记录更正

本条路（第 1、2 章）**未发现记录不实的条目**——逐条核对 `ROAD.md` 后，记录与实测一致，故不改动 `ROAD.md`。核对结论如下：

* ROAD.md 第 121 行 `[ ]` p.8.1.8（enum payload 二批 struct/fn）| 标记不变 | 记录称未落地 → 实测 `s2_9_struct.tie` 报 `E00365`，一致 | 证据：s2_9_struct.tie
* ROAD.md 第 312 行 `[ ]` p.9.10.10（dec 真小数）| 标记不变 | 记录称未落地 → 实测 `0.1d` 报 E00000、无 `d` 后缀，一致 | 证据：s2_16.tie
* ROAD.md 第 314 行 `[ ]` p.9.10.11（big 大整数）| 标记不变 | 实测 `big_parse` 报 E00489 未定义，一致 | 证据：s2_16b.tie
* ROAD.md 第 361 行 `[ ]` p.9.11.27（编译期值参数）| 标记不变 | 记录称「方向定稿、设计另出」→ 实测值参数前端可解析/实例化但后端 IR 失败（部分落地），未达「已落地」，`[ ]` 不构成不实 | 证据：v2.tie / v12.tie
* ROAD.md 第 363 行 `[x]` p.9.11.29（doc 注释 `///`）| 标记不变 | 记录已含 2026-09-27 补充，自述 `--dump-docs` 入口早于头部剥离故对含头部文件报 E00000 —— 本次实测完全复现，记录属实 | 证据：`--dump-docs s1_4b.tie`（无头部）成功、`--dump-docs s1_4.tie`（含头部）报 E00000
* ROAD.md 第 419 行 `[~]` p.9.13.5（并行数据流图）| 标记不变 | 记录自述「运算符形态留作后续语言档」→ 实测 `-\| <-\| ->x ~x -><` 全部报错，一致 | 证据：g1.tie / g3.tie / s1_12_not.tie
* ROAD.md 第 133 行 `[x]` p.8.2.3（字符串插值 `"Hello, {name}"`）| 标记不变 | 记录与**实现**一致（无前缀字符串确实插值，`s1_9_plain.exe` 输出「共 3 项」）；但与**规范** §1.9「须 h 前缀」冲突，属规范-实现冲突而非记录不实 | 证据：s1_9_plain.tie
* 无需更正但值得注意：ROAD.md 第 388 行 `[x]` p.9.12.6（行池）实测 ALL PASS；第 347 行 `[x]` p.9.11.17（函数类型）实测通过；第 349 行 `[x]` p.9.11.19（含 `0x_FF`）实测 255 —— 三者记录属实。

## 本路结论

1. **最严重的未实现（规范领先于实现）**：§1.9 `h"..."` 插值字符串 —— 规范本次修订新增必须 h 前缀，编译器把 `h` 当标识符，`h"共 {n} 项"` 报 `E00000`（lex_scan.tie:544-558 仅特判 `r`）。同源后果：规范要求「不带 h 的花括号即字面量」，而实现**默认插值**（`"共 {n} 项"` → 「共 3 项」），二者正面冲突。
2. **§2.16 精确数值类型整节未落地**：`0.1d` 字面量报 E00000（后缀白名单无 `d`）、`big_parse` 报 E00489、`div_ctx/half_even` 全仓无定义。规范给了完整语义与示例，实现为零。
3. **§2.18 值参数只落了前端**：`func zeros<N: i64>() -> array<f64, N>` 能解析并实例化（`zeros$n3`）但 IR 生成失败；值参数作数组长度（规范三例的核心）不可用；且顺带发现 **struct 的 `array<T,N>` 字段本身不被支持**（`struct Buf { var data: array<u8,4> }` 直接解析失败）。
4. **§2.3 宽类型只登记不落型**：`num/text/misc` 可作标注通过编译，但一旦参与运算/条件/格式化即报错（`num + i64` E00270、`misc` 作 if 条件 E00165），与规范「编译期类别名、按推导出的具体类型参与运算」相反。
5. **§1.12 运算符记号缺 4 组**：`~`（E00481 无法识别）、`..=`（切成 `..`+`=`）、`\` 解引用（实为内建 `deref()`）、图算子 `-\| <-\| ->x ~x -><`（全部报错；ROAD.md:419 自述运算符形态留作后续语言档）。另有 `?.` 属**死特性**：语法/推导齐备（须 struct 载荷），但 Option<struct> 被 enum payload 白名单拦截 → 报 E00365，实际不可用。
6. **规范与实现冲突（命名/行为层）**：① §1.1 文件名与头部角色不一致——规范要「警告 + 头部为准」，实现报硬错误 `E00000`（driver.tie:347）；② §2.11 转换函数名规范写 `to_i32/to_f64`，实现是 `as_i32/as_f64`（`to_*` 报 E00489）；③ §2.6/§2.9 规范示例语法（`return 1, 9`、`var lo, hi = …`、`Circle(r: f64)`）均不可编译，实现要求 `(1, 9)`、`var (lo, hi) = …`、无名 `Circle(f64)`；④ §2.5 规范示例 `age.has(k)` 不存在（E00475），成员判定用 `in`；⑤ §2.10 规范示例 `is_num(v)` 不存在（E00489）。
7. **规范自身内部矛盾**（建议上报修订）：§1.7 平衡三进制一行散文写「数字只用 0/1/2」，示例却是 `0t1T0`（含字母 `T`）——实现按散文（三进制 0-2，`0t120`=15），示例形式不可编译。
8. **规范缺口（实现有而规范未列）**：§1.6 关键字表遗漏 `extends`、`with`（二者在实现里是真保留字，`var extends = 1` 报 E00485；§1.12 表与 §6.5 正文却把它们当语法记号用）。另：§1.6 把 `run/self/type` 列为「用作标识符即报错」的保留字，实测三者均可作标识符（属位置识别），建议规范相应改述为上下文关键字。
