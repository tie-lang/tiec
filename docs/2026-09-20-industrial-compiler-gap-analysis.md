# tiec 对标工业级编译器差距分析 —— 功能/API 路线图输入
*EN: tiec vs industrial compiler gap analysis — input to the feature/API roadmap*

**日期** / Date: 2026-09-20 · **类型** / Type: 分析（对标 clang/GCC/rustc/go 类工业级编译器，梳理 tiec 缺失的功能与 API，作「为 tiec 添加更多 API」路线图的优先级依据）
**依据** / Basis: 用户方向（2026-09-20 定）"为 tiec 添加更多 API" · 设计文档 `tge/docs/designs/tedit-obfuscation-module-architecture.md`（§5 与此文同源，此处为 tiec 侧独立版本）
**关联** / Related: `tge/docs/designs/tedit-obfuscation-module-architecture.md`（compif 门面 + guard/forensic 双模组）· `docs/2026-09-18-compile-perf-regression-diagnosis.md`（性能病态诊断）· `compiler/driver.tie`（CLI/优化档）· `compiler/driver-lite.tie`（外部 opt/clang 依赖）· `compiler/frontend|middle|backend`
**版本** / Version: v0.1（初稿）

> EXEC BRIEF: tiec's language core already leads (multi-backend LLVM/trm/WASM,
> diagnostic-code system, deterministic fixed-point build gate, consteval). What
> it lacks is the **compiler-service / industrialization layer** — exactly the
> axis of "more APIs". Highest-value gaps, in order: language service / LSP,
> structured diagnostic output (JSON), incremental compilation caching, then
> middle-end optimization passes + LTO, self-contained toolchain (multi-target),
> sanitizers, compile-time reflection, fuzzing. The `compif` facade is the
> watershed from "can compile" to "can be consumed by tools".

---

## 1. 结论 / Conclusion

tiec 在「语言本体」层面已领先多数自研编译器；真正的空白在「**编译器服务化 + 工程化支撑**」这一整层——这正是"更多 API"的方向。`compif` 门面（见设计文档 §3）是把 tiec 从"能编译"推到"能被工具用"的分水岭。

## 2. 现状优势（不重复堆功能，先记已有点） / Existing Strengths

* **✔ 多后端**：LLVM 原生 / trm 字节码 / WASM（p.9.6.2 规划）
* **✔ 诊断标号体系**：C# 式五位数 `error[E#####]/warning[W#####]` + 建议（`diagcode`）
* **✔ 确定性构建**：自举不动点 SHA 门禁
* **✔ 编译期求值**：`consteval`（对标 constexpr / 编译期执行）
* **✔ 构建分层配置**：`-O0..-O3` / `--mem-limit` / `--profile` dev|release / `--target` / `--check-bounds` / `--shared`
* **✔ tieir 分发雏形**：`--tieir-out`（序列化）/ `--dump-irt`（读回）

## 3. 高优先缺口（补 API 即解，工具链层） / High-Priority Gaps

| 缺口 | 工业对标 | 说明 |
|---|---|---|
| **语言服务 / LSP** | clangd / rust-analyzer / gopls | 语义补全、go-to-def、悬停、引用、重构、inlay hints——需稳定 AST+符号+类型 API。**最大空白** |
| **结构化诊断输出** | clang `-fdiagnostics-format=json`、`--error-format`、多 span + `.help/.note/.suggestion` | 已有 diagcode（标号+建议），缺**机器可读 JSON 输出**与"报错后继续解析"的错误恢复 |
| **增量编译 / 构建缓存** | ccache / sccache / rust incremental | p.9.15.1 依赖感知缓存键是第一步；尚未到"改依赖才重编 / 产物复用" |
| **依赖文件 / 响应文件** | gcc `-MMD`（`.d`）、clang `@file` | 构建系统接入的硬需求 |

## 4. 中优先缺口（需新 pass / 新组件，编译器内核层） / Mid-Priority Gaps

| 缺口 | 说明 |
|---|---|
| **中端优化 pass** | `-O0..-O3` 只映射到后端（opt/clang）；中端 tie-IR 无自身优化（内联决策 / 常量折叠 / DCE / 循环优化）。代码生成质的缺口 |
| **LTO** | `--tieir-out` 有分发单元雏形，但跨单元 LTO（thin LTO 语义）未在 tiec 层接通 |
| **PGO** | `-fprofile-generate/-use` 类缺失（工业标配套件） |
| **属性标注** | `always_inline / likely / unlikely / noinline` 类 |
| **Sanitizer** | ASan / UBSan / TSan 集成；现仅有 `--check-bounds` |
| **编译期反射** | 枚举遍历 / 类型信息 / 属性内省缺失（`consteval` 是半个基础） |
| **源码文档生成** | rustdoc / javadoc 类缺失 |

## 5. 架构性缺口（最难补，需定心） / Architectural Gaps

* **✖ 自带工具链不自足**：`driver-lite` 依赖外部 `D:\LLVM\bin\opt/clang`。工业编译器自带 codegen + 链接驱动；不自足则难交叉编译、难分发
* **✖ 并行编译**：多文件并行 + 单文件内并行 pass 图。自举 10h 病态单靠缓存/增量不够，需并行（关联性能诊断文档）
* **✖ 调试信息一等公民**：DWARF 行号表 / `-g` 质量；现产物无符号表

## 6. 质量保证 / QA

* **✔** 回归门禁（diagcodes golden / s21 / 不动点）已有
* **✖ fuzzing / 差分测试**：csmith 式生成、diff testing、property-based——工业编译器有大量 fuzz + CI byte-diff

## 7. 优先级建议（对 API 路线图） / Suggested Priority

* **语义面 → 语言服务 / LSP** > 结构化诊断输出（JSON）> 增量编译缓存 > 中端优化 pass + LTO > 自足工具链 / 交叉目标 > sanitizer > 反射 > fuzzing

## 8. 落地对接口（与 design 文档 m 序列对齐） / Interface with Design Doc

* m1（`compif` 门面骨架 + tieir 往返）即**语义面 + 灯点亮语言服务的第一步**
* 结构化诊断输出（JSON / 错误恢复）可并入 m1 诊断访问器或独立小步
* 中端优化 pass + LTO 属新 pass 面，超出 `compif` 薄门面，需单独立项

---

## 附录 / Appendix

* 术语 / Terms：compif（编译器服务门面）· 中端优化 pass（middle-end optimization，tie-IR 层自身优化）· 语言服务（LSP）
* 演进：本文档为差距分析；落地进展随实现回写，与 tedit 设计文档保持同源同步