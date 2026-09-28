# tie 语言语法规范 × tiec 实现对账 —— 全 16 章逐条实现状态
*EN: tie Language Specification vs tiec implementation — per-clause implementation status across all 16 chapters*

**日期** / Date: 2026-09-27 · **类型** / Type: 审计（规范《tie 语言语法规范 2026.2》全 16 章逐条判定实现状态，判定一律以**实测编译**或**源码**为据）
**依据** / Basis: 规范正文 `tofflib/spec/ch01..ch16`（2026.2）· tiec 编译器源码（`compiler/`，约 10.8 万行 tie）· 测试语料（`tiec/tests/`，732 个 .tie）· 标准库（`tlib/std/`、`lib_v1/std/`）
**关联** / Related: `ROAD.md`（落地记录，**仅作线索，不作证据**）· `docs/2026-09-20-industrial-compiler-gap-analysis.md`（工业化差距分析）· `docs/designs/unsafe-credential-lock.md` 等设计稿
**版本** / Version: v1.0
**方法** / Method: 6 路并行审计 + 主代理亲验；判定口径见 §2；全部样例与原始报告留在 `tiec/_spec_audit/`

> EXEC BRIEF: Of 456 judgeable clauses across the 16 chapters, **278 are implemented (61%)**,
> 63 partially (14%), 97 not implemented (21%), 18 are non-spec statements. The language core —
> lexing, types, expressions, statements, functions, data structures, interfaces, modules,
> macros, unsafe/credentials — is largely landed. The two biggest voids are **Chapter 14
> (UI element blocks and graph syntax): 18 of 23 entries unimplemented, with `view` not even a
> keyword**, and the **numeric-precision cluster (§2.16 decimal `d`-suffix, bignum, §2.18 value
> parameters)**. Two defect classes matter more than missing features: **silent wrong values**
> (`1 << 4` in a `const` silently folds to 0; actor field initialisers silently discarded) and
> **compiler crashes** (`asm!` with an operand placeholder segfaults tiec). The spec also carries
> a distinct set of its own defects: examples that do not compile, tables that contradict the
> implementation, and three mutually inconsistent decompositions of the same feature.

---

## 1. 结论 / Conclusion

语言本体（词法、类型、表达式、语句、函数、数据结构、接口、模块、错误处理、宏、不安全机制、所有权）**实现度高**：第 1–13 章的 331 条可判定条目中，已实现 252 条（76%）。真正成片空白的是三处：

* **第 14 章界面元素块与图语法** —— 18 / 23 未实现，`view` 连关键字都不是；`type tie<ui>` 只是「登记后短路」。
* **数值精度族** —— §2.16 精确十进制（`d` 后缀）、大整数、显式除法精度三者在实现里为零；§2.18 编译期值参数只落了前端。
* **并发调度与重入** —— §10.4 / §10.9 任务图与图字面量、§10.7 `reentrant` 完全缺席（第 10 章 15 条里 7 条未实现）。

比「缺功能」更值得先处理的是两类**缺陷**：

* **静默错值**（编译通过、无诊断、值错）：全局 `const` 里的 `<< >> & | ^` 一律折叠为 `0`（`const TABLE_SIZE = 1 << 10` 得 0）；actor 字段初值被丢弃（`var n: i64 = 5` 经 `run C()` 读出 0）；变量→窄类型静默截断（`i64 300` 入 `i8` 得 44）。
* **编译器崩溃**：`asm!("mov {0}, 1", out(reg) n)` 令 `tiec.exe` 段错误（exit 139，零诊断）。

规范自身也有一批缺陷需修（不是实现的锅）：示例不可编译、**表与实现双向不符**（§1.6 关键字表、§1.12 记号表、§16.7 诊断编号分区表）、**同一写法给出三种互斥答案**（元组解构）、以及若干「正文讲了速查表没列 / 速查表列了正文没讲」的缺口。详见 §5–§7。

---

## 2. 判定口径 / Method

### 2.1 状态定义

| 状态 | 判据 |
| --- | --- |
| `已实现` | 语法被接受且语义/代码生成齐备；实测样例编译通过（必要时运行核验） |
| `部分实现` | 只有部分形态可用：仅解析不接受、仅某一子形态可用、语义范围收窄、或行为与规范不符 |
| `未实现` | 实测以语法/语义错误拒绝，或实现中找不到痕迹 |
| `非规范条目` | 设计立场 / 工程约定 / 文档说明，不含可编译的语言特性 |

### 2.2 证据等级

| 等级 | 形式 |
| --- | --- |
| A | 实测：写明样例文件、编译命令、结果（成功或 `error[Exxxxx]`） |
| B | 源码：`文件:行` 形式，指出实现所在函数 |

`ROAD.md` / `CHANGELOG.md` 的落地标记**一律不作证据**，只当「这里可能有东西可查」的线索——理由与实证见 §8。

### 2.3 三条实测纪律（本轮踩过的坑，后续复用请遵守）

1. **「grep 不到」不等于「不存在」** —— 库函数不在编译器源码目录。`trim` 曾被判「不存在」，实际由 **p.9.13.2 隐式前置**（`compiler/driver/prelude.tie`）暴露：`logic` / `script` 角色的文件会自动获得 `import "/std/prelude.tie" as lang` + `using lang;`，于是 16 个裸名（`trim` `trim_start` `trim_end` `to_lower` `to_upper` `starts_with` `ends_with` `str_has` `seq_has` `seq_index` `map_has` `map_cat` `tbl_cat` `clamp_i` `pow_i` `pow_i_checked`）可直接用。判「某函数不存在」前先查库根。
2. **「实测报错」可能是自己写法有误** —— 规范示例是散文式示意，未必逐字可编译。`actor` / `struct` 的字段在紧凑写法下需要分号（`parse_actor` 见 `frontend/pstmt_top_p3.tie:528`）；元组须带括号（`return (1, 9)` 而非 `return 1, 9`）。
3. **不要照抄规范示例来判特性存废** —— 规范示例本身可能引用不存在的 API。`map_new()` 与 `age.has(...)` 在实现里都**不存在**，据此曾误判「映射能力缺失」；实际映射（字面量创建、`map_has` 判键、`a + b` 合并、`a with { }` 更新）**全部可用**。凡「规范示例报错」，须先用实现能接受的等价写法建立正例，再区分「写法不同」（＝规范缺口）与「特性缺失」（＝未实现）。

### 2.4 两处影响判定口径的实现事实

* **部分检查默认关闭**：移动语义检查需 `TIE_MOVE_CHECK=1` 才报 `E00372`；遮蔽等警告需 `-w`；数组越界检查需 `--check-bounds`。按**默认** `tiec` 命令判「已实现」会漏判（这类条目一律记 `部分实现`）。
* **编译器自带前置**：`logic` / `script` 隐式获得 prelude 裸名（见上）；`class` 角色不注入（自举不受影响）。

---

## 3. 总览 / Overview

### 3.1 全章统计

| 章 | 已实现 | 部分实现 | 未实现 | 非规范条目 | 可判定合计 | 实现率 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 词法与记号 | 58 | 11 | 13 | 1 | 83 | 70% |
| 2 类型系统 | 40 | 4 | 10 | 0 | 54 | 74% |
| 3 运算符与表达式 | 8 | 6 | 2 | 0 | 16 | 50% |
| 4 语句 | 40 | 1 | 4 | 0 | 45 | 89% |
| 5 函数 | 33 | 5 | 6 | 0 | 44 | 75% |
| 6 数据结构 | 15 | 2 | 4 | 0 | 21 | 71% |
| 7 接口 | 9 | 1 | 1 | 1 | 12 | 75% |
| 8 错误处理 | 8 | 1 | 4 | 1 | 14 | 57% |
| 9 模块与导入 | 9 | 3 | 1 | 0 | 13 | 69% |
| 10 并发 | 5 | 1 | 7 | 2 | 15 | 33% |
| 11 不安全机制 | 16 | 3 | 8 | 2 | 29 | 55% |
| 12 宏与元编程 | 7 | 4 | 4 | 1 | 16 | 44% |
| 13 所有权与移动 | 3 | 1 | 2 | 1 | 7 | 43% |
| 14 界面元素块与图语法 | 2 | 1 | 18 | 2 | 23 | 9% |
| 15 工具链与语言服务 | 5 | 6 | 6 | 3 | 20 | 25% |
| 16 速查表（三方交叉核对） | 约 20 | 约 13 | 约 7 | 4 | 44 | — |
| **合计** | **278** | **63** | **97** | **18** | **456** | **61%** |

### 3.2 一句话印象

* 第 1–13 章（语言本体）：252 / 331 已实现（**76%**）。
* 第 14 章（界面/图）：**9%**，是全篇最薄的一章。
* 第 15 章（工具链）：真真假假——`tiec` 主链、静态库、`--emit-ir`、警告体系、REPL、**LSP（tsp.exe 实测可用）**为真；`--check` / `--emit-pdf` / `tiefmt` / `tielint` / `--dump-docs`（含头部文件）为假或残缺。

---

## 4. 逐章明细 / Per-Chapter Detail

> 每行一条独立可判定条目。证据列 `A:` 为实测样例（样例文件在 `tiec/_spec_audit/<路>/`），`B:` 为源码位置。
