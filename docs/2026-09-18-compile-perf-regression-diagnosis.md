# 编译性能倒退诊断存档 · tiec 自举 13min+ 卡死（内部档案）

*EN: Compile-Performance Regression Diagnostic Archive — tiec self-hosting stuck at 13min+ (internal)*

> **状态**：诊断中，根因收敛未定论（2026-09-18）。
> **目的**：内部诊断档案，记录本次编译性能倒退的排查过程、已确认事实、排除项与待办。
> 该内容仅供内部使用，不进入对外发行/文档面。
> **关联**：p.9.14 警告系统独立与性能优化（`tie-main/docs/designs/warning-system.md`）、
> p.9.15 编译器缓存重构 + 并行构建（`tie-main/docs/designs/compiler-cache-redesign.md`）。

---

## 一、症状

* tiec 自举（`tiec_nw.exe driver.tie -o tiec_new.exe`）**10 小时未完成**（bootstrap13，21:27 启动；
  单线程 CPU 满跑、I/O 为 0、RAM 从 21.5GB 降至 0.77GB、30 分钟零产物、无 clang 子进程 → 疑似死循环/病态超长循环）。
* 多次独立复测：`tiec.exe`/`tiec_nw.exe`/`tiec_wall.exe` 编译 driver 闭包均 **13min+ 未完**（CPU-bound，RAM 4.3GB）。
* 用户基准：早前编译（几个 G + 几十秒～几分钟）→ 现在（几十 G + 数小时），性能严重倒退。

## 二、可复现的耗时对照

| 输入 | 结果 | 结论 |
|------|------|------|
| `config.tie`（52KB 自包含，无 import） | **2.7s 完成** | 前端单文件不慢 |
| 510KB 单文件（irgen_expr 路径） | 24.6s 到语义错误 | 前端解析不慢 |
| 全 import 探针（11 顶层 import） | 29.5s 到语义错误 | import 展开不慢 |
| **driver 完整 import 闭包（~2.5MB）** | **13min+ 卡死** | 闭包全量语义+警告热路径慢 |

* 慢点在 **closing 全量语义/类型推断 + 警告检查**，非解析、非 import 展开、非后端链接。

## 三、已确认事实（可排除项）

* **与 p.9.15.1 缓存重构改动无关**——git stash 后纯 HEAD 编译同样慢。
* **与 --shared 修复无关**（irgen/llvmgen 改动同理被排除）。
* **纯 HEAD（09-17，无任何工作区改动）用 tiec.exe 编译 13min+ 未完** → 倒退源于**09-17 前端提交**。
* 09-17 提交共改 14 前端文件（+941 行）：pstmt_top +350 / lex_scan +198 / semantic +157 / sgen +67 /
  sinfer +17 / ast +4 / lex_state +6 / lex_symtab +4 / lex_tokdefs +30 / lexer +17 / scollect_port +11 /
  sstate +4 / parser +6 / irgen_agg +94。
  * 内容：p.9.11.28 return elision（等号体/单表达式体）、p.9.11.29 doc 注释 registry、
    p.9.11.30 三引号字符串、p.9.11.31 选择性导入（`sel_collect_refs` 树递归）、
    p.9.11.32 alias、p.9.11.33 struct `with`。
* **tiec_nw（--no-warn 预编译版，09-16 构建）另有内存 bug**：RAM 18-19GB（对照 tiec.exe 4.3GB），
  印证用户曾报 "--no-warn 内存飙 20G+"。普通编译/`-w` 路径不受此影响。
* 倒退回退逐一测试（pstmt_top→09-16、semantic→09-16）**仍慢**，未二分到底（因每次全量编译 13min+ 不可行）。

## 四、最可能根因（指针，未定论）

指向 **[p.9.14 警告链设计](./docs-desig)** 已登记的缺陷：
* `sm_warn_add` 内联在语义/类型推断检查点（semantic/sinfer/scheck，W00001-29），**零警告也付全量检查成本**；
* `;W:` 文本往返吞性能：`sm_ok_protocol` 拼 `;W:l c msg` 串 → `print_warns` find/strsub 再解析 →
  `diagcode.render_warning` 每条**二次 `normalize()`** + `+` 重建字符串 → O(n²)+双文本+重复归一化。

在 ~2.5MB import 闭包（数万 AST 节点）上放大成 13min+ / 4.3GB。

## 五、诊断阻塞

* **git 历史树对象损坏**：`git archive bbd22bb` / `git worktree add bbd22bb` 均
  `fatal: unable to read tree (db337d3b…)`，无法导出完整 09-16 树做干净对照。
* **每次全量编译 13min+**：二分回退测速（一次一文件换 09-16 版）不可行。

## 六、建议路径（待用户拍板）

* **先做 p.9.14 警告链提速**（p.9.14.1 结构化警告事件去 `;W:` 往返 + 独立非阻塞 pass），
  它既是编译慢的根，也是 **p.9.15 缓存重构能先成功编译一次的前置**（鸡生蛋阻塞）。
* 之后 p.9.15.1 缓存重构 + --shared 修复的 bootstrap/不动点验证才可行。

## 七、待验证清单（存档时未完成）

* --shared 修复：m2_md5 / density FFM 首调不崩 + 纯标量库不回归 + 自举不动点。
* p.9.15.1 缓存：多文件工程改依赖 → 重编；改无关文件 → 命中；自举不动点复核。
* p.9.14 警告链：警告渲染逐字节等价门禁 + 回归不劣化。

---

*EN: This is an internal diagnostic archive. Status: diagnosis in progress, root cause not
finalized (2026-09-18). Slowdown is in the import-closure full semantic/type-inference +
warning-check hot path (pointer to the p.9.14 warning chain). Recommended next: land warning
chain speedup first as a prerequisite to the p.9.15 cache redesign bootstrap.*