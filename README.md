# tiec

**tie 自举编译器** / *The tie self-hosted compiler*

tiec 是 tie 语言的编译器本体（与语言一体，品牌保留 tiec）：Keel 架构前端/中端/
后端 + 解释器 + 标准/扩展/精简库 + REPL + 构建回归脚本，0-Rust 自举（clone 后
用入库 stage0 `compiler/tiec.exe` 即可自举，无外部编译依赖；发行期捆绑 LLVM
精简工具链）。

*EN: tiec is the compiler of the tie language itself (kept as the tie brand):
Keel-architecture frontend/middle/backend + interpreter + std/ext/rdu libraries
+ REPL + build & regression scripts. 0-Rust self-hosting (clone and bootstrap
with the committed stage0 `compiler/tiec.exe`; no external build deps; bundled
with a trimmed LLVM toolchain at release).*

## 构建 / Build

```bash
compiler\tiec.exe examples\hello.tie   # 编译并运行示例
scripts\regress-s21.ps1 compiler\tiec.exe   # 自举验证 + 回归门禁
compiler\tiec.exe repl\repl.tie        # 无参数 → REPL
```

## 内容 / Contents

- `compiler/` 编译器全源码（frontend/middle/backend/interp/keel + `driver.tie`/
  `tdzd.tie`/`zdpub.tie` 等；`tiec.exe` stage0 引导二进制入库）
- `std/` `ext/` `rdu/` 语言标准 / 扩展 / 精简库
- `repl/` REPL 源；`prep/` 预处理与迁移工具
- `scripts/` 构建与回归脚本（bench、regress-*、selfhost-gate、zero-rust-check 等）
- `tests/` `examples/` 测试套件与示例源码
- `diagdocs/` 诊断标号数据（`diagcodes.data.tie` / `diagcodes.zd`）
- `sys/` 平台专用层（`sys/win32.tie` 命名空间 sys_win32）
- `archive/compiler-v1/` v1 编译器历史归档

## 相关组件 / Related components

- [tie-lang/tsp](https://github.com/tie-lang/tsp) — LSP 服务器（`tie --lsp`）
- [tie-lang/tpkg](https://github.com/tie-lang/tpkg) — 包管理器
- [tie-lang/tdb](https://github.com/tie-lang/tdb) — 数据库
- [tie-lang/vscode-tie](https://github.com/tie-lang/vscode-tie) — VSCode 扩展
- [tie-lang/tie-main](https://github.com/tie-lang/tie-main) — 聚合/发行仓

## License

本仓库按 **Tie Public License v2.0（TPL 2.0）** 授权发布（全文见 [LICENSE](LICENSE)）：
你可自由使用、修改并分发本软件源码，包括用于商业产品，仅需保留版权声明并附本许可证。

EN: This repository is released under the **Tie Public License v2.0 (TPL 2.0)**
(full text in [LICENSE](LICENSE)): you may freely use, modify, and redistribute
the source code, including in commercial products, provided you retain the
copyright notice and a copy of the license.
