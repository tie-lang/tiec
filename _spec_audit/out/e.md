# 路 E 审计报告 —— 第 14 章（界面元素块与图语法）、第 15 章（工具链与语言服务）、第 16 章（速查表）

审计对象：`tofflib/spec/ch14_ui.tie`、`ch15_tool.tie`、`ch16_ref.tie`
实现侧：`tiec/compiler/`（tiec.exe，自举 tie 编译器）
实测日期：2026-09-27　样例目录：`tiec/_spec_audit/e/`
命令模板：`/f/Projects/tie-repo/tiec/compiler/tiec.exe --no-cache <file> -o <file>.exe`

---

## 第 14 章　界面元素块与图语法

| 节 | 条目（规范要求） | 状态 | 证据 | 备注 |
| --- | --- | --- | --- | --- |
| 14.1 | 元素块以 `@` 引入（`@ window "设置" { … }`） | 未实现 | A: s14_1.tie（函数内）→ `error[E00000] @5:5: 无法以 Token104 开始表达式`；s14_1b.tie（顶层）→ `error[E00453] @4:10: 悬空注解：@注解后必须是函数、struct 或 enum 声明` | 实现里 `@`=lex_at(tag 104)，**仅**作「声明前置注解」（lex_tokdefs.tie:100；pstmt_top.tie:270→parse_annotated_decl；pstmt_top_p1.tie:255）。元素块语法不存在 |
| 14.1 | 元素嵌套由书写层次表达（不需括号配对） | 未实现 | 同上（无元素块解析路径） | — |
| 14.2 | 属性 `@ label title`（名称与值） | 未实现 | A: s14_2.tie → `error[E00000] @5:5: 无法以 Token104 开始表达式` | `@` 在语句位置整体不可解析 |
| 14.2 | 表达式属性用花括号界定（同插值串花括号） | 未实现 | A: s14_2.tie 同上 | — |
| 14.3 | 事件 `on_事件名: 函数值` 绑定 | 未实现 | A: s14_3.tie → `error[E00000]`（Token104） | — |
| 14.3 | 事件接受具名函数与短闭包 | 未实现 | A: s14_3.tie 同上 | 短闭包本身可用（见 16.10 块管道），但事件绑定位置无解析 |
| 14.4 | 界面元素引用作用域值、按引用关系局部刷新 | 未实现 | A: s14_4.tie → `error[E00000] @5:5`（Token104） | 刷新范围（增量重建）在实现中无对应机制 |
| 14.5 | 图语法 `graph N { node a … a -> b }` | 未实现 | A: s14_5.tie → `error[E00000] @5:11: 期望 语句结束符，实际是 标识符 'Pipeline'` | `graph` 非关键字（key 表无 graph），`graph` 被当标识符 |
| 14.5 | 边附加条件 `parse -> store when valid` | 未实现 | A: s14_5.tie 同上（未达该行） | — |
| 14.5 | 图作为值可构造/组合/执行（不可变，组合产新图） | 未实现 | A: s14_5.tie 同上 | — |
| 14.6 | 界面单元 `view V(p) -> (Act) { @Column { } }` | 未实现 | A: s14_6.tie → `error[E00000] @4:1: 顶层只允许函数定义、import、using、struct、enum、命名空间声明、extern 声明、全局变量或宏定义，实际是 标识符 'view'` | **`view` 不是关键字**：`lex_symtab.tie:36 build_kw()` 71 项表内无 `view`；全仓 grep 无 `view` 关键字/节点/处理（Grep `\bview\b` 于 compiler/ 零命中）。属「完全未实现」，非「按文本特判」 |
| 14.6 | 单元分类表（视图/组件/样式/主题/动作） | 非规范条目 | — | 概念/立场表，无可编译特性 |
| 14.7 | 元素内穿插原生控制流（条件/遍历在界面里） | 未实现 | A: s14_7.tie → `error[E00000] @6:5: 无法以 Token104 开始表达式` | — |
| 14.7 | 元素内容两种形式：字面量省括号、表达式保留括号 | 未实现 | A: s14_7.tie 同上 | — |
| 14.8 | 修饰链 `@Text "标题" .title` / `.muted` / `.lg` | 未实现 | A: s14_8.tie → `error[E00000] @5:5: 无法以 Token104 开始表达式` | — |
| 14.8 | 事件箭头 `@Button "+1" .lg -> Inc` | 未实现 | A: s14_8.tie 同上 | 箭头 `->` 本身可用（管道），但元素位无解析 |
| 14.8 | 分层 `@layer base, components, overrides` | 未实现 | A: s14_8.tie 同上 | — |
| 14.8 | 作用域 `@scope Card { .title { 前景: 表面色 } }` | 未实现 | A: s14_8.tie 同上 | — |
| 14.8 | 主题 `@theme dark { 表面色 = 深灰900 }` | 未实现 | A: s14_8.tie 同上 | — |
| 14.8 | 层顺序覆盖规则（后声明层覆盖先声明层） | 非规范条目 | — | 规则陈述，无对应实现机制 |
| 14.6（文件级） | 文件角色 `type tie<ui>` 可写 | 部分实现 | A: s14_ui.tie / s14_ui_win.tie 编译通过，输出 `[预处理] 识别为 ui 界面文件（头: …），已转交 UI 工具链 —— v0.1 UI 工具链尚未实现`，**不产出任何产物**；B: role_reg.tie:49 `reg_base("ui","pass","window,web,embedded")`；driver.tie:369-388 `disp=="pass"` → 打印转交提示后 `return 0` | **「登记」≠「生效」**：`ui` 只在角色表登记 + 头部识别通过，随后 driver **短路退出**，既不改变解析、也不改变代码生成。规范 §14.6 要求界面单元参与编译，实现未接。**tiu 库存在 ≠ 文件级 UI 语法可用**（tiu 是独立 UI 框架仓，与 `type tie<ui>` 语法无关） |
| 对照 | `@注解(3)` 声明前置注解（`@` 的真实用途） | 已实现 | A: s16_annot2.tie / t16_annot3.tie → `编译成功`；B: pstmt_top_p1.tie:255-318 parse_annotated_decl（仅 func/struct/enum，参数限字面量） | 与元素块同符不同义 |
| 对照 | `#[unsafe.share]` 声明属性（`#` 的真实用途） | 已实现 | A: s16_attr.tie / t16_attr2.tie → `编译成功`；B: lex_tokdefs.tie:73 `lex_hash=91`；pstmt_top.tie:251；pstmt_top_p1.tie:238-246 白名单仅 `unsafe.{share,trm,mem,ext}` | 非白名单属性报「未知属性」 |

> 本章：已实现 2 / 部分实现 1 / 未实现 18 / 非规范条目 2

---

## 第 15 章　工具链与语言服务

| 节 | 条目（规范要求） | 状态 | 证据 | 备注 |
| --- | --- | --- | --- | --- |
| 15.1 | 编译六阶段（预处理/词法与语法/语义分析/中间表示/优化/生成） | 非规范条目 | B: 实现为 keel 分派驱动——driver/pipeline.tie:500-520 注册真实 pass `kpass_front/irgen/tieir/emit/link/trmemit` | 阶段名与实现命名不一致（实现无「优化」独立阶段名，opt 在 link 前由外部 opt.exe 承担），但属工程说明，无编译特性可判 |
| 15.1 | 语义分析检查顺序固定（类型→约定→所有权/捕获） | 非规范条目 | — | 顺序性主张，无对外可观测接口可判 |
| 15.2 | `tiec app.tie` 编译为可执行文件 | 已实现 | A: s16_*.tie 多例 → `编译成功` | — |
| 15.2 | `tiec lib.tie -o lib.a` 编译为静态库 | 已实现 | A: `tiec s15_lib.tie -o lib.a` → `库编译成功: lib.a`（636B） | class 角色，role_reg.tie:43 output=lib |
| 15.2 | `tiec app.tie --emit-ir` 只产出中间表示 | 已实现 | A: `--emit-ir -o s15_ir.ll` → `已生成 LLVM IR: s15_ir.ll`（157KB） | cli_args.tie:24/73 |
| 15.2 | `tiec app.tie --check` 只做检查 | 未实现 | A: `--check` → `error[E00362]: 参数错误。输入 tiec --help 查看用法。` | 仅存在于 `driver-lite.tie`（T2.9 雏形入口）与 `proto/main.tie`，**主 tiec 未接线**；`--help` 亦不列 |
| 15.2 | `tiec app.tie --emit-pdf` 随产物输出结构报告 | 未实现 | A: `--emit-pdf` → `error[E00362]: 参数错误` | 全仓无 `--emit-pdf` 字样 |
| 15.2 | 优化级别与目标平台作命令行开关 | 已实现 | A/B: `--help` 列 `-l<0-3>`/`-t<0-3>`/`--target`/`--profile`/`--backend` 等 | — |
| 15.3 | 诊断有稳定编号 + 类别 + 坐标 | 部分实现 | A: `error[E00000] @5:5: 无法以 Token104 开始表达式`；B: diagcode.tie:277-290 `render_error` 格式为 `error[E#####] @行:列: 名；尾段。` | 编号存在（目录 E00001–E00649 连续）；但**坐标无文件名**（规范 §15.3 写 `main.tie:12:5:`）；**类别不编码进编号**（见 §16.7 行） |
| 15.3 | 诊断样例 `error[E00387] …缺少第 2 个形参…` | 部分实现 | B: diagcode_cat.gen.tie:791 `E00387` = 「命名实参调用%缺少第%个形参%的值」 | 编号与消息均存在；渲染为 `error[E00387] @行:列: …`，无 `文件名:` 段 |
| 15.3 | 诊断样例 `warning[W00008] …变量 'tmp' 未被使用` | 已实现 | A: `tiec -w s15_warn.tie` → `warning[W00015] @4:5: 可变绑定未修改；…`、`warning[W00005] @4:5: 未使用变量；…`；B: diagcode.tie:409 `W00008`=变量遮蔽、:403 `W00005`=未使用变量 | W 编号体系（W00001–W00029）真实在册；**注意**：规范示例把「未使用变量」记作 W00008，实现里 W00008 是「变量遮蔽」，「未使用变量」是 **W00005** → 规范示例编号错配 |
| 15.3 | 诊断撰写三约定（位置/期望-实际/给修法） | 非规范条目 | — | 写作约定，无编译特性 |
| 15.4 | `tiefmt src/` 独立格式化工具 | 未实现 | A: 全仓 `find -iname tiefmt*` 零命中，`which tiefmt` 无 | 仅有 tsp `format.tie` 提供 LSP `documentFormatting`（能力广告存在），无独立 CLI |
| 15.4 | `tielint src/` 独立静态检查工具 | 未实现 | A: 全仓 `find -iname tielint*` 零命中，`which tielint` 无 | 静态检查的**一部分**内嵌于 tiec（`-w/--warn` 触发 W00001–W00029），但无 `tielint` 入口 |
| 15.5 | `///` 文档注释提取 + 与声明一起生成 API 文档 | 部分实现 | A: **提取可用**——`tiec s15_doc_noheader.tie --dump-docs` → `共 1 条声明 doc: [5] gcd: …`；**但**同一内容加必需头部 `type tie<logic>` 后 `tiec s15_doc.tie --dump-docs` → `error[E00000] @1:1: 顶层只允许函数定义…实际是 标识符 'type'`；B: driver.tie:262-268 `--dump-docs` 在**头部扫描/strip_type_header 之前**短路，直接 `parser.parse_ast(src)` | doc 注册表落地（lex_tokdefs.tie:310-369），**文档生成器不存在**（无 API 文档产出工具）。`--dump-docs` 对含头文件（即所有合法 tie 文件）报错 → 记录不实，见「记录更正」 |
| 15.5 | 文档注释支持与正文相同的排版记号 | 未实现 | B: doc 文本按行 trim 后原样入注册表（lex_tokdefs.tie:310-327），无排版记号解析 | — |
| 15.6 | 交互式环境 `tie`（REPL）接受表达式并立即求值 | 部分实现 | A: `repl.exe` → `1 + 1`⇒`2`、`len(xs)`⇒`3`，与规范「同一套语义」相符；**但规范示例 `xs -> sort` ⇒ `变量 'sort' 未声明`**（内置函数不能作管道目标） | REPL 真实存在且可求值；规范示例用了不可用的写法。另：EOF 后空转刷 `>`（健壮性缺陷） |
| 15.6 | REPL 用法示例 `xs -> sort` → `[1, 2, 3]` | 未实现 | A: 见上，`变量 'sort' 未声明` | 与主代理确证的「内建函数不能作管道目标」一致 |
| 15.7 | 语言服务（补全/跳转/悬停/实时诊断） | 部分实现 | A: `vscode-tie/vendor/tsp.exe` 真实存在；LSP `initialize` 返回完整 capabilities（hover/definition/references/signatureHelp/documentSymbol/rename/completion/documentFormatting/foldingRange/semanticTokens）——见 `lsp_probe.py` 输出；B: driver.tie:99/196-197 `--lsp` 接线、cli_args.tie:83；tsp/（server.tie/protocol.tie/analyze/completion/nav/refactor/sigdoc/format/tokens） | 核心能力真实落地，**非空白**（与 ROAD「自认 LSP 是最大空白」的记录相反，记录不可信）。但 `textDocumentSync:1`＝**Full 同步**，规范称「按文件增量重算」不成立 |
| 15.7 | 编辑器诊断编号与命令行一致 | 部分实现 | B: tsp 复用 tiec 前端（tsp/analyze.tie 调 tiec 前端）；编号同源 | 合理，但未逐条实测两端一致 |

> 本章：已实现 5 / 部分实现 6 / 未实现 6 / 非规范条目 3
> （已实现：15.2×4 + 15.3 warning×1；部分：15.3×2 + 15.5 doc + 15.6 + 15.7×2；未实现：15.2 --check + 15.2 --emit-pdf + 15.4×2 + 15.5 文档生成 + 15.6 示例；非规范：15.1×2 + 15.3 约定）

---

## 第 16 章　速查表 × 规范正文 × 实现（三方交叉核对）

| 速查表条目 | 出处（§16.x） | 正文是否有定义（哪节） | 实现是否支持 | 结论 |
| --- | --- | --- | --- | --- |
| `type tie<ui>` / `type tie<db>` / `type tie<port>` / `type tie<ir>` | 16.1 | ch14 §14.6 | 头部识别 ✓；`ui`/`db`/`port`/`zd`/`data`/`tsh` = pass 短路（driver.tie:370-388）；`ir`→check；`class`/`type`→lib；`logic`/`script`→exe | 部分实现：角色头可写可识别，多数领域角色仅「转交提示」不产出；规范未说明该差异 |
| `var / const / func / pub func / struct / enum / namespace / port / impl / actor / macro / import` | 16.2 | ch02/05/06/07/09/10/12 | A: t16_12b.tie ✓（除 enum 见下） | 已实现 |
| `enum E { A(x: i64) }`（**命名**变体字段） | 16.2 / 16.12 | ch02 | ✗ A: t16_12a.tie → `error[E00484] @13:13: 期望 ')'，实际是 Colon`；B: pstmt_top_p4.tie:7 头注释 `VariantB(i64, string)`＝**位置式** | **规范内部/规范-实现不一致**：实现只接受 `A(i64)` 位置式；速查表与正文写命名式。`if let Some(v) = opt`（16.11）按位置绑定可用 ✓ |
| `extern func e(a: i64) -> i64` | 16.2 / 16.12 | ch09 | ✗ A: `extern func` → `error[E00001] @4:1: extern 声明必须跟 'fn'，实际是 Func`；`extern fn` → `error[E00077] @4:1: extern 声明必须标注 unsafe（unsafe extern fn e(...)）` | **关键字错 + 前置条件缺**：实现要求 `unsafe extern fn`。速查表「func」应为「fn」且未写 `unsafe` |
| `func f(a: i64)` / `ref` / `immut` / `move` 三种前缀 | 16.3 | ch05 §5.x / ch13 | A: t16_3b.tie ✓（ref/immut/move 均通过；ref 另受「须动态表」语义约束 E00590） | 已实现 |
| `b: i64 = 10` 默认值（须连续居尾） | 16.3 | ch05 | A: t16_3b.tie `f5(a:1)` ✓ | 已实现 |
| 命名实参 `f(a: 1, c: 3)` 跳过 b | 16.3 | ch05 | A: t16_3b.tie `f5(a: 1)` ✓ | 已实现 |
| `rest: ...i64` 变长参数 | 16.3 | ch05 | A: t16_3c.tie ✓ | 已实现 |
| `a -> f` 管道 | 16.4 | ch03 | A: t16_pipe.tie ✓ | 已实现（但**内建函数不可作管道目标**，主代理已证 E00488） |
| `t -> t + 1` 短闭包 | 16.4 | ch05 §5 捕获 | A: 块形式 `3 -> { x -> x + 1 }` ✓（t16_10b3）；裸形式 `t -> t+1` 作独立值 → E00488「未声明变量 t」（缺目标类型） | 部分实现：需类型上下文；规范未注明 |
| `x in m` / `x not in m` | 16.4 | ch03 | A: t16_4i.tie ✓ / t16_4g.tie ✓ | 已实现 |
| `v ?: 10` 安全默认值 | 16.4 | ch03 | 部分：A t16_4b.tie → `error[E00100] @6:13: '?:' 左侧必须是 Option<T>（Some/None 形态枚举），实际是 i64` | 部分实现：仅 Option 左值；速查表未写前置条件 |
| `v?` 存在判定 | 16.4 | ch03 | 部分：A t16_4c.tie → `error[E00223] @6:8: '?' 解包的操作数必须是 Result/Option 枚举，实际是 i64` | 部分实现：仅 Option/Result；速查表未写前置条件 |
| `p\` 解引用 | 16.4 | ch11/unsafe | ✗ A: t16_4f6.tie `var y = p\` → `error[E00204] …实际返回 ptr<i64>`（未解引用）；t16_4f4.tie → `error[E00602] 类型不匹配…表达式是 ptr<i64>` | **未实现**：`\` 在实现里只是**二元整除**（pexpr_p1.tie:396 `lex_backslash`→B_IDIV），无一元解引用形态。实现提供 `deref(addr_of(x))`（t16_4f5.tie ✓，需 unsafe） |
| `n %% 1` 「原地修改」 | 16.4 | 与 16.10 冲突 | A: t16_4d.tie ✓（作为表达式语句被接受，仅求值不改原值） | **规范内部矛盾**：§16.4 说 `%%`＝原地修改，§16.10 说 `a %% b`＝成对（floor）取余。实现是后者（B_FLOORMOD，pexpr_p1.tie:393-395）。「原地修改」无实现 |
| `a ** b` 幂 / `a **? b` 带检查幂 | 16.4 / 16.10 | ch03 | A: t16_4e.tie ✓（两式均通过） | 已实现 |
| `0..10  0..=10` 范围 | 16.4 / 16.10 | ch03 | A: `0..10` 在 `for` 中 ✓（t16_5a）；**`0..=10` ✗** t16_4h.tie → `error[E00000] @6:16: 无法以 Eq 开始表达式`；`var b = 0..10` 作独立值 → 中间优化失败（LLVM opt error: `'%2' defined with type 'i64' but expected 'ptr'`） | 部分实现：仅**左闭右开 `..`**，无 `..=`；且范围作**值**（非 for 头）生成坏 IR |
| `if / while / for … in / for c in s.chars() / lbl: … break lbl / switch / return / break / continue / goto / panic` | 16.5 | ch04 | A: t16_5a/5b/5c/11_switch/11_switchexpr 均 ✓（`s.chars()`✓、`lbl:`+`break lbl`✓、`panic("msg")`✓） | 已实现 |
| `yield v` | 16.5 / 16.11 | ch05 | A: t16_11_yield3.tie ✓（生成器函数 `-> i64` 元素类型）；带值 `return v` 在同函数内 → `error[E00538] 生成器函数不允许带值 return` | 已实现（有约束，速查表未写） |
| `println/to_string/str_len/len/str_char/char_code/table_new_i64/table_push` | 16.6 | ch03/ch06 | A: t16_6a.tie ✓ | 已实现 |
| `map_new()` 新建映射 | 16.6 | **正文无任何节定义 `map_new`** | ✗ A: t16_6_map.tie → `error[E00489] @5:13: 未定义的函数 'map_new'` | **规范缺口 + 未实现**：速查表凭空出现（线索成真）；正文亦无定义 |
| `file_read/file_write/byte_read/byte_write/load_library/get_proc/dyn_call` | 16.6 | ch11 | 未逐条实测（超本路范围） | 待复核 |
| 诊断编号分段表（E00000-99 语法词法 / E00100-199 内建调用 / E00200-399 类型调用 / E00400-499 导入声明作用域 / E00500-699 借用移动捕获 / E00700+ 并发宏不安全） | 16.7 | ch15 §15.3 | ✗ B: `diagcode_cat.gen.tie` 头注释明示「**标号规范：五位纯序号 E00001 起全局连续；家族仅记 JSON/td family 字段，不编码进标号**」；目录 = E00001–E00649 **按消息字节序连续**，无 E00700+；`diagcodes.data.tie` family 独立为 `1 词法 / 2 语法 / 3 语义 / 4 运行时 / 5 CLI / 6 后端 / 7 REPL / 8 LSP / 9 内部` | **规范与实现根本不符**。反例：`E00422`「字符字面量只能包含一个字符」是**词法**错却落在声称的「400-499 导入声明作用域」；`E00164`「#cfg 条件块未闭合」（预处理/语法）落在声称的「100-199 内建函数调用形态」；`E00372`「变量已移动」落在 300s 而声称「500-699 借用移动捕获」；`E00100`「?: 左侧须 Option」落在 100s；**E00700+ 区间不存在**（max E00649） |
| `if c {} else if … else {}` / `if let Some(v) = opt {}` / `lbl: for … { break lbl }` / `switch v { case 1: … default: … }` / `var x = switch v { 0 -> a, _ -> b }` / `var (a, b) = pair` / `var (a, ...rest) = xs` / `guard c else { return }` / `defer { … }` / `try { x = f()? }` / `return`/`yield`/`break`/`continue` / `panic("msg")` | 16.11 | ch04/ch05 | A: t16_11_iflet2.tie ✓（`if let Some(v)`）、t16_11_switchexpr.tie ✓、t16_11_rest.tie ✓、t16_11_guard.tie ✓、t16_11_defer.tie ✓、t16_11_switch.tie ✓ | 已实现（`var (a,b)=pair` 与 `var (a,...rest)=xs` 形式可用；注意主代理证 `return 1, 9`、裸 `var lo,hi=`、`var (a,b)<-` 均 ✗） |
| `unsafe goto #tag`（配 `#[tag.tag]` 标签） | 16.11 | ch11 §7.1.5 | 部分：A t16_11_goto2.tie → `error[E00066] @7:9: goto 只能在 unsafe 上下文使用`；t16_11_goto3.tie → `error[E00195] @8:13: goto 目标 '#done' 在外层块但位于 goto 之后（只能向后跳到已执行的外层块头，R2）`；t16_11_goto4.tie（标签先于 goto，向后跳）✓ | 部分实现：存在但有约束（须在 unsafe 块/unsafe 函数内；只能**向后**跳到已执行外层块头；标签须 `#[tag.名字]`）。速查表未写约束 |
| `unsafe { }` 不安全块 | 16.11 | ch11 | A: t16_11_goto4.tie、t16_4f5.tie ✓ | 已实现 |
| `[pub] [unsafe] [async] [inline] func` / `func f(x) -> i64 = x * 2` / `struct S<T> extends B` / `namespace` / `port P { pub func m(self) -> i64 }` / `interface I { pub func m(self) }` / `impl P for S` / `actor A { var n: i64 = 0 }` / `macro m(x: code) -> code` / `alias M = table<f64>` / `import "m.tie" as m` / `import "m.tie".{ a, b }` / `pub import "m.tie"` / `using ns.sub` / `var g: table<i64> = []` / `const K: i64 = 10` | 16.12 | ch05-12 | A: t16_12b.tie ✓（pub/inline func、等号体、struct extends、namespace、port、interface、impl、actor、macro、alias、using、全局 var、const）；选择性导入 t16_imp2.tie ✓、`pub import` t16_imp3.tie ✓、`using m` t16_imp4.tie ✓ | 已实现（`import "…" as m` 语法被接受；对**无 namespace 的模块**作 `m.f()` 限定调用 → `error[E00391] 命名空间函数 'm::alpha' 未定义`，属语义面，另见 ch09 路） |
| `@注解(3)` | 16.12 | ch15 §15.3（@注解 p.9.11.12） | A: t16_annot3.tie ✓（非关键字注解名）；关键字作注解名（如 `@inline`）→ `error[E00485] 期望标识符，实际是 Token102` | 已实现（注解名不能是关键字；速查表未写） |
| `#[属性]` | 16.12 | ch11 | A: t16_attr2.tie `#[unsafe.share]` ✓；B: 白名单仅 `unsafe.{share,trm,mem,ext}`（pstmt_top_p1.tie:238-246） | 部分实现：仅 unsafe 域白名单，其它属性报「未知属性」 |
| `#cfg(cond)` | 16.12 | ch15 §15.3（p.9.11.13） | 部分：A s16_cfg.tie（裸式）→ `error[E00164] @3:1: #cfg 条件块未闭合（缺少 #end/#endif）`；s16_cfg2.tie（`#cfg(debug) … #end`）✓ | 部分实现：真实形态须 `#end`/`#endif` 闭合、单层不可嵌套、条件限 `key=value`/`debug`/`release`/`!x`。速查表写裸 `#cfg(cond)` 不完整 |
| `view V(p: i64) -> (Act) { @Column { } }` 界面单元 | 16.12 | ch14 §14.6 | ✗ A: s14_6.tie → `error[E00000] … 实际是 标识符 'view'`（`view` 非关键字） | 未实现（正文列出、速查表列出、实现无） |
| `a +? b   a -? b   a *? b` 带检查算术 / `a << b a >> b a & b a \| b a ^ b` / `cond && cond` / 比较 | 16.10 | ch03 | A: t16_10g.tie ✓（+?/-?/*?/&&/<<&/\|/^ 全通过） | 已实现 |
| `a \ b` 整除 / `x \= v` 整除复合赋值 | 16.10 | ch03 §3 整除 | A: t16_10a2.tie ✓、t16_base.tie ✓ | 已实现 |
| `x %%= v` 成对取余复合赋值 | 16.10 | ch03 | ✗ A: t16_10a3.tie → `error[E00000] @6:9: 无法以 Eq 开始表达式`（`%%` 与 `=` 未合成 `%%=`） | 未实现：token 表有 `\=`（lex_backslasheq=109）但**无 `%%=`**。速查表列了 |
| `v -> [i]` 管道进下标 / `v -> .field` 管道进字段 / `v -> { x -> e }` 块管道 | 16.10 | ch03 | A: t16_pipe.tie ✓（`xs -> [1]`）、t16_10b4.tie ✓（`p -> .x`）、t16_10b3.tie ✓（`3 -> { x -> x+1 }`） | 已实现 |
| `x <- v` 反向赋值 | 16.10 | ch03 | A: t16_10_rev.tie ✓（`x <- 5` 后 `x==5`） | 已实现（`lex_larrow`=95） |
| `(a, b) <- t` 解构 | 16.10 | ch03 | A: t16_10_destr3.tie ✓（**裸形式**，`a`/`b` 须先声明）；**`var (a, b) <- f()`** → `error[E00484] @9:16: 期望 '='，实际是 InterpL`；`var (a, b) = f()` → 编译成功（t16_11_pair.tie） | 部分实现：§16.10 裸形式 ✓；正文 §3.11 的 `var (a,b) <-` 形式 ✗。解构三种写法中只有**裸 `(a,b) <- t`** 与 **`var (a,b) = f()`** 可用，正文 §2.6 `var lo, hi = f()` 与 §3.11 `var (a,b) <- f()` 均不可用 → 规范内部三处不一致 |
| `v with { k: x }` 不可变更新 | 16.10 | ch06 | A: t16_10d3.tie ✓ | 已实现 |
| `opt ?   opt ?: d   obj?.f   obj?[i]` 可空链 | 16.10 | ch03 | 部分：A t16_10c3.tie → `p?.f` 报 `error[E00100] '?.'：左侧必须是 Option<T>…实际是 P`；`?:`→E00100、`?`→E00223（均要求 Option/Result） | 部分实现：全部要求 Option/Result 左值；速查表并列书写易误读为对所有类型可用 |
| `xs[1..3]   xs[..2]   xs[2..]   xs[..]` 切片 | 16.10 | ch03 | A: t16_10f.tie ✓（四式全通过） | 已实现 |
| `\p` 解引用（不安全） | 16.10 | ch11 | ✗ A: t16_4f7.tie → `error[E00000] @8:17: 无法以 Token108 开始表达式`（Token108=lex_backslash） | 未实现（同 §16.4 `p\`） |
| `1_000_000` / `42i32 0x80u16 1.5f32 0.1d` / `42 0xFF 0b1011 0o755` / `3.14 1.5e3` / `'A'` / `"…"` `h"{…}"` `r"…"` 多行串 | 16.9 | ch01 | A: t16_9.tie ✓（除 `0t1T0`） | 已实现 |
| `0t1T0` 三进制字面量 | 16.9 | ch01 | ✗ A: t16_9_tern.tie → `error[E00000] @5:21: 期望 语句结束符，实际是 标识符 'T0'`（`0t1` 被截断，`T0` 当标识符） | 未实现：**类型 `trit` 与字面量后缀 `1t/0t/-1t` 可用**（t16_9_trit.tie ✓），但 `0t…` 三进制**字面量**语法不存在 |
| `-1t  0t  1t` 三值 | 16.9 | ch01 | A: t16_9_trit.tie ✓ | 已实现 |
| 16.8 设计要点回顾 / 16.13 形式与分工表 | 16.8 / 16.13 | 立场汇总 | — | 非规范条目（立场/对照表，无编译特性） |

> 本章：可判定条目 44 项中——已实现约 20 / 部分实现约 13 / 未实现约 7 / 非规范条目 4
> （未实现集中在：`map_new`、`p\`/`\p` 解引用、`x %%=`、`0t…` 三进制、`..=` 闭区间、`view`、命名式 enum 变体；部分实现集中在：`?:`/`?`/`?.` 仅 Option、goto 约束、`#cfg` 块、`#[属性]` 白名单、范围作值坏 IR、extern 需 unsafe fn）

### 三类缺口（最典型例）

**A. 速查表列了、正文没讲**（规范缺口）
* `map_new()`（§16.6）——正文任何节无定义，实现报 `E00489 未定义的函数 'map_new'`。
* `x %%= v`（§16.10）、`0t1T0`（§16.9）——正文 ch01/ch03 亦无对应定义节，速查表孤立出现。

**B. 正文讲了、速查表漏了**（规范缺口）
* §15.2 正文称「优化级别与目标平台属于命令行开关」，速查表 §16 无命令行表；实现在册开关达 20+ 个（`--check-bounds/--ffast-math/--visibility/--shared/--tieir-out/--dump-irt/--profiling` 等），速查表只提 `-o/--emit-ir/--check/--emit-pdf`。
* §16.7 只给「错误区间」，未给**警告区间**归类依据；实现 W00001–W00029 且规范 §15.3 示例把「未使用变量」写成 W00008（实现为 W00005）。

**C. 速查表与正文/实现写法不一致**（规范内部 + 规范-实现）
* `extern func e(...)`（§16.2/§16.12）vs 实现 `unsafe extern fn`（`E00001`/`E00077`）。
* `enum E { A  B(x: i64) }` 命名变体（§16.2/§16.12）vs 实现位置式 `A(i64)`（`E00484`），且 §16.11 `if let Some(v)` 位置绑定才可用。
* 解构：§16.4/§16.10 `(a, b) <- t` vs §16.11 `var (a, b) = pair` vs 正文 §2.6 `var lo, hi = f()` vs §3.11 `var (a,b) <- f()` —— 四种写法并存，实测**仅**裸 `(a, b) <- t`（先声明目标）与 `var (a, b) = f()` 可用；`var lo, hi =`、`var (a,b) <-` 均 ✗。
* `n %% 1 // 原地修改`（§16.4）与 `a %% b // 成对取余`（§16.10）自相矛盾。
* `p\`（§16.4）与 `\p`（§16.10）两种解引用记号并存，实现**都不支持**（`\` 已是整除二元运算符）。

---

## 记录更正

> 本路按团队约定**不改 `ROAD.md`**，仅提建议，由主代理集中处理。

| ROAD 行号 | 原标记 → 建议新标记 | 原记录说法 → 实测结论 | 证据 | 处置建议 |
| --- | --- | --- | --- | --- |
| ROAD.md 第 363 行 | `[x]` → 保持 `[x]`，但需加限定 | 「p.9.11.29 doc 注释 /// … **[已落地 2026-09-17，tiec 0786441：doc 注册表 + pdoc_* 查询接口 + `--dump-docs`]**」→ doc 注册表与查询接口确已落地，但 **`--dump-docs` 对任何带必需头部 `type tie<…>` 的文件报错、无法使用**（头部扫描/strip 在短路之后），仅对**无头文件**可用 | A: `tiec s15_doc_noheader.tie --dump-docs` → `共 1 条声明 doc: [5] gcd: …`；`tiec s15_doc.tie --dump-docs` → `error[E00000] @1:1: 顶层只允许函数定义…实际是 标识符 'type'`；B: driver.tie:262-268 | 建议在 363 行末追加：`**记录更正 2026-09-27**：--dump-docs 对含 type 头的文件不可用（头部扫描前短路），仅无头文件可用（证据：s15_doc.tie / s15_doc_noheader.tie）` |
| — | — | ROAD 称「**LSP 是「最大空白」**」（引自 gap 分析口径）→ 实测 **tsp.exe 真实存在且 LSP initialize 返回完整 capabilities**（补全/hover/定义/引用/签名/符号/重命名/格式化/语义 token） | A: `lsp_probe.py` 对 `vscode-tie/vendor/tsp.exe` initialize 输出（Content-Length 790，capabilities 完整）；B: driver.tie:99/196、cli_args.tie:83、tsp/server.tie | 记录口径偏保守/不实，建议按实测改述为「LSP 核心能力已落地，增量重算与全能力稳定性待验」 |
| — | — | 无 ROAD 条款声称 `type tie<ui>` 文件级界面语法已落地（tiu 是**独立 UI 框架库** p.9.4，与 `type tie<ui>` 语法无关）→ 实测 `type tie<ui>` 仅头部识别后短路，元素块/view/graph 无任何实现 | A: s14_ui.tie 输出「UI 工具链尚未实现」；s14_1…s14_8 全部报错；B: role_reg.tie:49、driver.tie:370-388 | 无需改 ROAD；但请主代理确认 ch14 在 ROAD 中确无「已落地」误标（本路未检出对应行） |

> 本路**未改**任何 ROAD.md / CHANGELOG.md / 规范文件；所有发现均以实测或源码为据。

---

## 本路结论

1. **第 14 章整体是「规范先行、实现为零」**：§14.1–14.8 的 18 个可判定条目**全部未实现**——`@` 元素块、属性、事件、图语法、`view` 界面单元、元素内控制流、修饰链、`@layer/@scope/@theme` 无一可用。`@`(tag 104) 在实现里**只**作声明前置注解（`parse_annotated_decl`），`#`(tag 91) **只**作 `unsafe.*` 白名单属性，二者都不是元素块记号。

2. **`type tie<ui>` 属「登记了但未生效」的典型**：`ui` 在 `role_reg.tie:49` 登记（output=`pass`）、头部识别通过，随后 `driver.tie:370-388` **短路打印「v0.1 UI 工具链尚未实现」并 `return 0`**，既不改变解析也不产出任何产物。**tiu 库存在 ≠ 文件级 UI 语法可用**。

3. **`view` 不是关键字（决定性证据）**：`lex_symtab.tie:36 build_kw()` 71 项表中无 `view`，全仓 grep 零命中，实测顶层 `view Counter(…)` 报 `E00000 … 实际是 标识符 'view'`。属**完全未实现**，非按文本特判。

4. **第 15 章工具链「一真一假」两头**：**真**——`tiec` 主链、`-o lib.a` 静态库、`--emit-ir`、内置警告（W00001–W00029）、REPL（可求值）、**LSP（tsp.exe 实测可 initialize，能力齐全）**；**假**——`--check`/`--emit-pdf` 报 `E00362`、`tiefmt`/`tielint` 独立工具不存在、`--dump-docs` 对含头文件不可用。

5. **§16.7 诊断编号分区表与实现根本不符（最严重规范缺陷）**：实现按**消息字节序连续**编号 E00001–E00649，**family 不编码进标号**（catalogue 头注释自述）；**E00700+ 区间不存在**。反例明确：词法错误 `E00422` 落在「导入声明作用域」区间、预处理错误 `E00164` 落在「内建函数调用」区间、`E00372`「已移动」落在「类型与调用」区间。另注：§15.3 示例把「未使用变量」写作 `W00008`，实现中 W00008 是「变量遮蔽」、W00005 才是「未使用变量」。

6. **§16 速查表三类缺口确证**：①速查表凭空出现且未实现——`map_new`（`E00489`）、`x %%=`（`E00000`）、`0t1T0`（`E00000`）、`p\`/`\p` 解引用；②正文讲、速查表漏——命令行开关表、警告编号依据；③速查表与实现写法冲突——`extern func` vs `unsafe extern fn`、命名式 enum 变体 vs 位置式 `A(i64)`、`n %% 1` 原地修改 vs `a %% b` 取余自相矛盾。

7. **最严重的 5 项未实现**（对用户影响排序）：① 第 14 章整章界面/图语法（含 `view`）不可用；② `map_new` 及 §16.6 映射能力缺失（速查表承诺、实现 `E00489`）；③ `p\`/`\p` 解引用记号不存在（仅 `deref(addr_of())`，需 unsafe）；④ `x %%= v`、`0t1T0`、`0..=10` 三处语法缺失；⑤ 工具链 `--check`/`--emit-pdf`/`tiefmt`/`tielint`/`--dump-docs`（含头文件）缺失。

8. **记录可信度**：ROAD 对 LSP 的「最大空白」表述**低估**（实测可用）；对 `--dump-docs` 的「已落地」表述**高估**（含头文件即报错）。二者均未改文件，仅在「记录更正」给建议。
