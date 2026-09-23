# tiec/tools —— 开发工具 / Development tooling

> 本目录存放**开发期**使用的脚本：自举不动点校验、大文件拆分器、仓库对象库修复。
> EN: Development-time scripts: fixed-point bootstrap check, oversized-file splitters,
> and odb repair. None of them ship with the compiler.
>
> 所有脚本的仓库根一律取自环境变量 `TIEC_ROOT`，未设置时用当前工作目录，便于换机使用。
> EN: Every script resolves the repo root from `TIEC_ROOT` (falls back to the cwd).

## 一、自举不动点校验 / Fixed-point bootstrap check

```sh
sh tools/fp.sh [输出目录]        # 默认 ../_tiec_verify/fp
```

三阶不动点：`tiec.exe` 编 driver → n1 → n2 → n3，`SHA(n2) == SHA(n3)` 即达成。
约 100 秒；输出目录默认在仓库外侧，避免污染工作树。
EN: Three-stage bootstrap; a matching n2/n3 hash means the fixed point holds.

## 二、拆分器 / Splitters（`tools/split/`）

全部为通用器：只搬「函数 + 其紧邻上方注释块」，绝不搬 `import` / 顶层全局 `var` /
`namespace` 包裹行，并输出函数集完整性校验（前集必须 ⊆ 后集）。

| 脚本 | 适用形态 | 用法 |
|---|---|---|
| `split_parts.py` | 文件过大、函数可整块搬走（**命名空间感知**，顶层函数保持顶层身份） | `python split_parts.py plan\|apply <相对compiler的路径> [每片预算行]` |
| `split_dispatch.py` | `if <VAR> == <整数> { ... }` 巨型调度器按分支提取 | `python split_dispatch.py plan\|apply <路径> <函数名> <分派变量> <落盘文件>` |
| `split_branch_blocks.py` | **语句级**提取：任意条件的 `if ... { ... }` 平铺分支（`split_dispatch.py` 只认整数字面量链） | `python split_branch_blocks.py plan\|apply <路径> <函数名> [前缀] [预算] [分片名]` |
| `split_builtin_branches.py` | `builtin_expr` 式 `if nm == "名字"` 分支提取（按段注释归域） | `python split_builtin_branches.py plan\|apply` |
| `split_expr_files.py` | 按域把大文件里的函数搬到多个新文件（一次性记录，范式参考） | `python split_expr_files.py plan\|apply` |
| `split_driver.py` | `driver` 同命名空间跨文件范式（flat / ns 两种风格） | `python split_driver.py plan\|apply <组名,…>` |

`split_branch_blocks.py` 的安全判据（不满足就跳过该分支，绝不硬搬）：

* 分支体最后一条顶层语句必须是 `return`（否则「贯穿到下一分支」的语义会丢）；
* 分支不读取兄弟语句声明的局部（函数前置 `var` 除外——会被原样复写进提子函数）；
* 分支自己声明的局部不得被分支外读取（比对时**跳过字符串内容与 `ns.member` 调用**，
  否则消息串里的 `{k: v}`、`types.is_map` 会被误判成耦合）；
* 沿用原函数的形参表与返回类型（`check_stmt(s)` 不能写成 `(id)`）。

环境变量：`TIEC_ROOT` 仓库根；`TIE_SPLIT_EXCLUDE` 逗号分隔的不搬函数名（`split_parts.py`）。
EN: `split_parts.py` is the generic namespace-aware function packer; the other four are
shape-specific extractors kept as working references.

### 拆分铁律 / Splitting rules（实测总结）

* `else-if` 链与多行条件块必须**整块**搬（含起始 `if` 与闭合 `}`），切短会把后续函数吞进体内。
* 与相邻语句共享局部变量时按**区域**搬（向上吞并紧邻 `var`/注释，向下到下一个同级块起点）。
* 花括号计数必须**字符串/注释感知**（源码里 `{` 常出现在注释与字符串中）。
* 拆出文件只含函数与注释：不含 `import`、不含顶层全局 `var`（globals 与 import 树留主文件）。
* `namespace X {` **之前**定义的函数是顶层函数，被其他 ns 裸名调用——分片必须按各函数
  自身的命名空间上下文包裹，否则报「未定义函数」。
* 分片文件绝不覆盖既有分片（用 `_qN` 而非复用 `_pN`）；改完必须做函数集完整性校验。
* `main` 必须留在顶层（放进 `namespace` 会链接期缺入口）。
* 每次改动后 `grep` 核验标记存在（替换不匹配会静默跳过）。

## 三、审计 / Audits

```sh
python tools/func_len.py [仓库根] [上限]     # 单函数行数审计（默认 300 行）
python tools/orphan_check.py [仓库根]        # 列出没有任何文件 import 的源码（孤儿）
```

`func_len.py` 的花括号计数对字符串与注释感知（源码里 `{` 常出现在字符串/注释中）；
`orphan_check.py` 只报告不删除——入口文件、`_` 探针、独立自检本就无人 import。
EN: `func_len.py` audits the per-function line limit; `orphan_check.py` reports
unreferenced sources, leaving the deletion decision to you.

## 四、对象库修复 / odb repair

```sh
python tools/repair_objects.py <秒预算> [缺失 blob 清单]
```

本机删除被重定向到回收站，`git` 的「先删旧 pack、后写新 pack」类操作一旦被 120 秒上限
打断会掏空对象库；该脚本按内容校验（`git hash-object -w` 必须复现原 SHA）从 blobless
partial clone 与 GitHub REST API 两路回填缺失对象。
EN: Rehydrates blobs missing from the local odb, content-verified against their SHA.

## 五、其它 / Others

* `repair_objects.py` 的 `TIEC_PARTIAL` / `TIEC_REPOS` / `TIEC_GH` 等环境变量见文件头注释。
* 复现探针放在 `tiec/tests/_p*_probe/`（例如 `_p921_interp_flag_probe/flag_nested_if.tie`
  记录解释器「标志位 + 嵌套 if/else 不终止」缺陷）。
