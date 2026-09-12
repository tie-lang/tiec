# p.9.1.1 内置库补全清单（Builtin Library Catalog）

> 持久化蓝图文档（Blueprint catalog）。本页只定**清单**，不实现、不建仓。
> 每个候选库对应一个子项编号，落地实现计入后续 p.9.1.x 批次。
> This page only defines the **catalog** — it implements nothing and creates no
> registry entry. Each candidate library is assigned a sub-item id and lands in a
> later p.9.1.x batch.
>
> - 日期 Date：2026-09-13
> - 分支 Branch：p.7
> - 归属 ROAD：p.9.1 内置库补全 + 编译体验（本页为子项 **p.9.1.1**）

---

## §0 摘要 / Summary

std/ 与 ext/ 已覆盖：数据结构、字符串/Unicode、文件/路径、网络/HTTP、
WebSocket、正则、JSON/XML/TOML/CSV、SQLite、时间、随机数、全套密码学
（哈希/对称/非对称/椭圆曲线）、压缩（brotli/lz4/zstd）、图像（png/jpeg/svg/qr）、
HTML、TLS、GUI（gfx, 基于 skia）、爬虫（spidey）、向量检索（vecsearch）、
LLM/日志/测试/模板等。

缺口（Gap）聚焦在 **多媒体编解码（webp/avif/音频/视频）** 与若干工程便利库
（zlib/gzip、JSON5、完整 datetime、GIF、色彩管理等）。本清单按 ROAD 提示与
现状缺口，罗列 14 个候选库，按 **高 / 中 / 低** 三档优先级推进。

std/ and ext/ already cover data structures, string/Unicode, fs/path, network/HTTP,
WebSocket, regex, JSON/XML/TOML/CSV, SQLite, time, RNG, a full crypto suite
(hashes/symmetric/asymmetric/ECC), compression (brotli/lz4/zstd), images
(png/jpeg/svg/qr), HTML, TLS, GUI (gfx on skia), crawler (spidey), vector search
(vecsearch), LLM/logging/testing/templating, etc.

The **gap** centers on multimedia codecs (webp/avif/audio/video) plus a few
engineering conveniences (zlib/gzip, JSON5, a full datetime, GIF, color management,
etc.). This catalog lists 14 candidate libraries, prioritized **高 / 中 / 低**
(High / Medium / Low).

---

## §1 现状盘点 / Current Inventory

### 1.1 std/（标准库，trade 核心）

| 类别 Category | 库 Libraries |
| --- | --- |
| 数据结构 Data Struct | collection, deque, set, graph, radix, sort, optsearch, intern, result, tpl |
| 字符串/Unicode String/Unicode | string, utf, ascii, format, pretty(ext) |
| 数值/数学 Numeric/Math | math, exmath, bigint, linalg, bytes |
| 文件/系统 FS/System | fs, path, process, cron, db, version, args, stdio |
| 网络 Network | net, dns, http, httpc, http_server, ws, smtp |
| 编码 Serialization | json, csv, encoding, diff |
| 模板/标记 Template/Markup | tpl, markdown |
| 时间 Time | time |
| 随机/哈希 RNG/Hash | random, csprng, xxh3, siphash, md5, sha1, sha256, sha512, sha3, shake, blake2, blake3, hmac, hkdf, pbkdf2, poly1305, ascon_mac |
| 加密/签名 Crypto | crypto, ed25519, ecdsa_p256, x25519, base48, jwt |
| 其它 Misc | llm, tsha1/tsha1_w48（大 SHA 性能表） |

### 1.2 ext/（扩展库，分发为类/库）

| 类别 Category | 库 Libraries（namespace） |
| --- | --- |
| 压缩 Compression | codec: brotli, lz4, zstd, compress |
| 图像 Image | png, jpeg, svg, qr |
| 配置 Config | config: toml |
| 标记/文档 Markup/Doc | html(dom/entities/select/token/text/links), xml(xml/tree) |
| TLS/证书 TLS | tls(der/ca/chain/x509/tls1_2/tls1_3/aead/gcm/p256/tool) |
| 密码算法 Sym/Asym | aes, chacha20, argon2, scrypt, ascon_aead, ecdsa |
| GUI | gfx（skia/win 窗口、layout、event，经 thunk_binding / unsafe FFI） |
| 爬虫 Crawler | spidey(crawl/polite/robots/seen) |
| 向量检索 VectorSearch | vecsearch(flat) |
| 工具 Util | cache, log, test, bench, pretty, ml, registry, tui |

### 1.3 既有实现形态参考 / Existing Implementation Shapes

- **纯 tie 实现（主流）**：png、zstd、lz4、brotli、jpeg（在下为教学/简化但格式自洽）、
  tls、xml、html、qr、svg 等。数据平面沿用「table<i64> 字节表 / 逗号分隔序列」惯例，
  位流/熵编码自写（如 png 自写 DEFLATE 解码 + zlib 包装）。
- **C 绑定（unsafe FFI，少量）**：`ext/gfx` 经 `skia/thunk_binding.tie` +
  `thunk/gen_thunk.tie` 桥接外部 skia（生成 thunk 存根，driver ↔ FFI 层）。

后续补全也遵循这两档落地路径：**纯 tie 优先；重/慢或规格庞大者用 unsafe FFI 绑定已成熟 C 实现。**

Pure-tie is the default; heavy or spec-huge codecs use unsafe FFI to bind mature C
implementations (mirroring how `ext/gfx` rides on skia via thunk).

---

## §2 补全清单 / Candidate Catalog

> 一库一子项。编号：`p.9.1.1.<n>`（候选库是 p.9.1.1 模块的子项）。
> 优先级：**高/中/低**（功能性排序，不用字母+数字伪标签）。
> 落地路径：纯 tie = 自写；C = unsafe FFI 绑定。
> One library per sub-item — `p.9.1.1.<n>`. Priority is **高/中/低**.
> Path: 纯tie = hand-written; C = unsafe FFI binding.

| 编号 # | 库 Library | 优先级 Pri | 依赖 Deps | 理由 Rationale | 落地路径 Path |
| --- | --- | --- | --- | --- | --- |
| p.9.1.1.1 | **zlib/gzip（deflate/inflate）** | 高 | 无（自写 RFC 1951） | HTTP/gzip、PNG 已自含、未来打包/指纹格式的公共底座；现仅有 brotli/lz4/zstd | 纯tie（复用 ext/png 的 inflate 经验） |
| p.9.1.1.2 | **WebP 解码**（→编码） | 高 | 自写 VP8 或 C: libwebp | ROAD 多媒体提示；ext 已有 png/jpeg 无 webp | 纯tie 起步，渐进可加 C 绑定 |
| p.9.1.1.3 | **AVIF 解码** | 高 | C: libavif/libaom（HEIF+AV1） | ROAD 多媒体提示；压缩率现代的图片目标 | C 绑定（unsafe FFI） |
| p.9.1.1.4 | **datetime（完整日期时间）** | 高 | 复用 std/time | 现 time 仅时间戳；缺时区/日历/解析/格式化 | 纯tie |
| p.9.1.1.5 | **GIF 编解码** | 高 | 自写 LZW | png/jpeg/svg 已具备，GIF 补齐简单动画/索引图 | 纯tie |
| p.9.1.1.6 | **JSON5** | 中 | 复用 std/json 解析骨架 | JSON 超集（注释/尾逗号/单引号/无引号键），配置与手写文件友好 | 纯tie |
| p.9.1.1.7 | **音频编解码（WAV 纯tie；MP3/FLAC/Ogg C 绑定）** | 中 | WAV 自写；MP3/FLAC 用 dr_libs/FFmpeg | ROAD 音频提示；WAV 简单先纯tie，有损/压缩走成熟库 | WAV 纯tie + 有损 C 绑定 |
| p.9.1.1.8 | **视频容器解析（MP4/MKV）** | 中 | 复用 zlib/big endian 工具 | ROAD 视频提示；先解析器（读写容器），编码/完整解码后续 | 纯tie 解析器 + 可选 C: FFmpeg |
| p.9.1.1.9 | **regex-pro（正则增强）** | 中 | 复用 std/regex | 现有 regex 偏基础；补前瞻/回引用/Unicode 类/惰性用于工程解析 | 纯tie |
| p.9.1.1.10 | **xlsx（Excel 读取）** | 中 | 依赖 p.9.1.1.1 zlib + ext/xml | 表数据交换刚需；xlsx = zip(xml)，两端做薄 | 纯tie |
| p.9.1.1.11 | **color（色彩管理）** | 中 | 无；供 gfx/图像 | sRGB/Linear/灰度/ICC 简表；图像与 UI 统一色彩 | 纯tie |
| p.9.1.1.12 | **rng-adv（统一随机/密码学封装）** | 低 | 复用 std/random+crypto | 现在 random/csprng 分散；聚合成统一种子/接口 | 纯tie |
| p.9.1.1.13 | **QR 解码（读取）** | 低 | 依赖 ext/qr | ext/qr 现仅生成；读取补闭环 | 纯tie |
| p.9.1.1.14 | **BMP 编解码** | 低 | 无 | 极简无损位图格式，教学/工具链兜底 | 纯tie |

> 注：ROAD 提示的 WebP/AVIF/音频/视频 = 子项 .2/.3/.7/.8，均为高~中优先。
> The ROAD-mentioned webp/avif/audio/video map to .2/.3/.7/.8 (high~medium).

---

## §3 优先级与推进顺序 / Priority & Sequencing

- **第一梯队（高）**：zlib/gzip(.1)、WebP(.2)、AVIF(.3)、datetime(.4)、GIF(.5)。
  网络与图片是最高频，且 zlib 是一批后续（xlsx）依赖的底座。
- **第二梯队（中）**：JSON5(.6)、音频(.7)、视频容器(.8)、regex-pro(.9)、
  xlsx(.10)、color(.11)。
- **第三梯队（低）**：rng-adv(.12)、QR 解码(.13)、BMP(.14)。

推进顺序原则：**高优先纯tie 项先行**（自写、无外部运行时、可立即集成），
C 绑定项（AVIF）需先落 thunk/FFI 脚手架（复用 ext/gfx 的 gen_thunk 流程）。

Sequencing rule: high-priority pure-tie items ship first (no external runtime,
immediately integrable); C-bound items (AVIF) require the thunk/FFI scaffold reused
from ext/gfx.

---

## §4 落地形态约定 / Landing Conventions

1. 每个库独立 document/namespace，命名如 `std/zlib.tie` / `ext/webp/webp.tie`。
2. 数据平面按现状惯例：多字节/非文本用 `table<i64>` 字节表 + 逗号分隔序列传参；
   位流/熵编码/CRC 自实现（对齐 ext/png）。
3. C 绑定项走 `ext/gfx` 的 thunk 模式：`gen_thunk` 生成存根 → `thunk_binding.tie`
   unsafe FFI → 对外纯 tie 接口。
4. 实现批次（后续 p.9.1.x）按高→中→低顺序进入，每库一个独立 commit + 探针测试。

各子项真实实现随后续批次落地；本清单保持为唯一优先级真相源（single source of truth）。
Actual implementation of each sub-item lands in later batches; this catalog stays the
single source of truth for the backlog & priorities.