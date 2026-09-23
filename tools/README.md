# tiec/tools —— 开发工具（100% tie / Development tooling, pure tie）

> 本目录存放**开发期**使用的工具，全部为 tie 实现（编译型 `tie<logic>` 程序）；
> 脚本一律走 `scripts/*.tsh.tie`（tshell）。**禁止 Python / shell 脚本**——
> 工具链自身也是 tie dogfood 的一部分（2026-09-23 用户拍板：100% tie）。
> EN: Development-time tools, all written in tie and compiled by tiec itself;
> scripts live in `scripts/*.tsh.tie` (tshell). Python/shell scripts are not
> allowed - the toolchain is part of the tie dogfood (user decision, 2026-09-23).
>
> 仓库根取自当前工作目录（在 repo 根运行）；编译方式：
> `compiler\tiec.exe tools\<名>.tie -o <tmp>\<名>.exe`。

## 一、自举不动点校验 / Fixed-point bootstrap check

见 `scripts/bootstrap-fp.tsh.tie`（tshell 脚本）：

```sh
tsh_main.exe -f scripts\bootstrap-fp.tsh.tie [输出目录] [fresh]
```

三阶不动点：`tiec.exe` 编 driver → n1 → n2 → n3，n2 与 n3 逐字节一致即达成
（certutil 求 SHA256 只比哈希行）。约 100 秒；输出目录默认在仓库外侧。
三阶各约 35 秒——单命令 120 秒上限内跑不完三阶时，脚本按产物**断点续跑**
（传 `fresh` 强制全部重跑）。
EN: Three-stage bootstrap; matching n2/n3 hashes mean the fixed point holds.
Stages resume from existing artifacts so no single command exceeds the
2-minute limit; pass `fresh` to rebuild everything.

## 二、审计工具 / Audits（编译型，原生速度）

| 工具 | 用途 | 用法 |
|---|---|---|
| `func_audit.tie` | 超 300 行函数审计（D4） | `fa.exe [上限]`（默认 300） |
| `orphan_check.tie` | 没有任何文件 import 的源码（G8 孤儿） | `oc.exe` |
| `visibility_survey.tie` | 各命名空间 pub / 私有函数分布（II1 诊断） | `vs.exe` |

三者共用同一套原语：`exec_output`（`dir /s /b` 取文件清单）、`file_read`、
字符串/注释感知的花括号计数、逐函数回溯所属命名空间（**不要用括号深度栈
逐行归类**——tie 源码缩进不规则且存在零缩进 `if`，实测会撕碎归属）。
`orphan_check` 的路径归一化必须先 `/`→`\` 再切段（import 目标用正斜杠、
`dir /s /b` 用反斜杠，不统一则 `.` 段切不出来）。
EN: All three scan `compiler/` with string/comment-aware brace counting and
the backward namespace attribution verified during the G1/G2 splits.

## 三、历史拆分工具的去向 / Where the old splitters went

p.9.21.2/3 的大文件拆分（G1）曾用一次性 Python 工具辅助，现按 100% tie 约束
移出仓库（git 历史可考）；拆分时踩坑总结沉淀为**规则**（见下），未来若需
再拆，按规则用 tie 重写工具。
EN: The one-shot Python splitters used during the G1 splits were removed per
the pure-tie decision (see git history); their lessons survive as the rules
below.

### 拆分铁律 / Splitting rules（实测总结）

* `else-if` 链与多行条件块必须**整块**搬（含起始 `if` 与闭合 `}`）。
* 与相邻语句共享局部变量时按**区域**搬，或就地保留。
* 花括号计数必须**字符串/注释感知**。
* 拆出文件只含函数与注释：不含 `import`、不含顶层全局 `var`。
* `namespace X {` 之前定义的函数是顶层函数，跨 ns 裸调依赖其顶层身份。
* 分片文件绝不覆盖既有分片（用 `_qN`）；改完做函数集完整性校验。
* `main` 必须留在顶层（放进 ns 会链接期缺入口）。
* 分片 import 插在 `namespace` 行**之前**（ns 体内只允许函数/类/嵌套 ns）。
* 顺序流水线型长函数（非分派链）**不能**机械切段：局部变量跨段共享且表
  按值传参，必须按语义段落手工提取并逐段 regress。

## 四、odb 修复 / odb repair（过程记录，工具已移除）

2026-09-16 的 repack 中断曾掏空本机对象库；当时用 Python 工具回填了 33/36
个对象（其余 3 个服务端已 404）。修复过程等价于：

1. `git fsck --connectivity-only` 收集缺失对象清单；
2. 对每个缺失 blob：`gh api repos/<owner>/<name>/git/blobs/<sha>` 取
   base64 → 解码 → `git hash-object -w --stdin`，**写回前必须哈希校验**
   （复现原 SHA 才落库）；commit/tree 走 `/git/commits` / `/git/trees`；
3. 清理指向不可恢复对象的悬空 reflog。

预防：`git config gc.auto 0`、`maintenance.auto false`（本机删除被重定向到
回收站，「先删旧 pack 后写新 pack」类操作被 120 秒中断会掏空对象库——严禁
在本机仓库跑 `git gc` / `git repack` / `git prune`）。

## 五、复现探针 / Reproduction probes

复现探针放在 `compiler/tests/_p*_probe/`（例如 `_p921_interp_flag_probe/flag_nested_if.tie`
记录解释器「标志位 + 嵌套 if/else 不终止」缺陷）。
