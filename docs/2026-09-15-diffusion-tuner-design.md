# 微型扩散定调器设计 / Micro Diffusion Terrain Tuner Design

日期 / Date: 2026-09-15 · 仓库 / Repo: tiec（tie 侧）· Subterra（融合侧）· 编号 / Items: p.9.14.x

## 目标 / Goal

用 tie 编写一个小型扩散模型，引导 Subterra 地形生成，保障宏观地形的**整体性**（大陆连片、海岸线连贯、山带成系、海陆比例自然）；Subterra 的微观地形与洞穴仍由噪声算法生成，保证速度与性能。

EN: Write a small diffusion model in tie that guides Subterra terrain generation for macro coherence (connected continents, coherent coastlines, mountain belts, natural land/sea ratio), while Subterra keeps its noise algorithms for micro terrain and caves to preserve speed and performance.

## 参考 / Reference

[xandergos/terrain-diffusion](https://github.com/xandergos/terrain-diffusion)（SIGGRAPH '26 / arXiv:2512.08309）：*coarse map 程序化草图 → 小型扩散模型精炼 → 无限世界逐 patch 确定性采样*。本设计取其两层结构并简化：tie 内自包含、确定性、O(1) 随机访问、零外部依赖。

EN: Follows the two-stage structure of Terrain Diffusion: procedural coarse sketch → small diffusion model refinement → infinite-world per-tile deterministic sampling, simplified to be self-contained in tie with determinism and O(1) random access.

## 总体架构 / Architecture

```
离线训练（tiec 仓, exe）                          运行时（Subterra DLL, 自包含）
─────────────────────────────                    ──────────────────────────────
macro_gen 合成地质先验数据集                          ┌─ tile 缓存（全局 table, 固定槽位）
   ├ 条件草图 c_cont/c_mtn（低频噪声）               ├─ sample(): 确定性 DDPM 反演
   └ 理想化目标 elev/mtn（锐海岸/山带/海陆）           │   （seed 派生 Rng + strat=false）
diffunet 微型 UNet（4→4→8 通道, 16×16）             ├─ forward(): 自包含 conv/convT/GN
   ├ forward（与运行时 copy 逐位一致校验）            └─ coarse_elev/coarse_mountain(x,z,seed)
   └ backward（训练）                                  │      → 查缓存 + 双线性 + 边缘交叉淡化
trainer: add_noise → UNet → MSE → backward → adamw       ▼
weights: 训练后经代码生成器输出 `*.gen.tie` 字面量   surface_height = sea + elev·24
                                                      + landMask·(mtn·15 + noise_hills·5)
                                                      （hills/caves 仍为纯噪声）
```

## 组件 / Components

* **macro_gen（p.9.14.1）**：结构化宏观图生成器。条件草图 = 与 Subterra 现 `continent()/mountain()` 同族的低频 fbm 价值噪声；理想化目标 = 对草图施加地质变换（海岸幂律锐化、山带沿海岸距离带成系、海陆掩码），使每个训练样本全局连贯。
* **diffunet（p.9.14.2）**：微型 UNet。输入 4 通道（2 条件 + 2 加噪目标）×16×16 = 1024，恰好等于 tie 容量池上限；down 16→8、bottle 8×8×8、convT 上采样、groupnorm、t 标量通道偏置；总参数约 1k。forward + backward 成对（基于 std/nn）。
* **trainer（p.9.14.3）**：DDPM 条件训练（std/diffusion schedule + add_noise、loss.mse、optim.adamw）。训练后代码生成器输出权重字面量 `*.gen.tie`（沿用 diagcodes 生成器先例）。
* **sampler（p.9.14.4）**：确定性采样（seed 派生 Rng、`strat=false`），双线性上采样、边缘交叉淡化到连续条件草图（保证 tile 边界 C0 无接缝）。
* **运行时模块（p.9.14.5）**：`subterra_diffuse` 自包含 forward（与训练 copy 逐位一致，探针校验）、tile 缓存（全局 table、预分配固定槽位、幂等写、多线程安全）、导出 `stdens$coarse_elev/coarse_mountain(x,z,seed)`、融合进 `surface_height`。

## 关键数字 / Key Numbers

* tile = 512×512 方块，潜在网格 16×16 单元 → 单元 = 32 方块；`array<f32,1024>` 单张量 ABI 契合。
* UNet 参数 ≈ 1k；单 tile 采样 10 步 ≈ 3M flops，均摊每列 < 15 flops（可忽略）。
* 缓存 6×6 tile ≈ 150KB；每列查询 = 1 次缓存命中 + 双线性。
* 权重 1k 个 f32 字面量（.gen.tie 约 12KB）直接编进 DLL，零文件加载、零外部依赖。

## 确定性 / Determinism

* 世界种子 + tile 坐标经 hash3 派生 Rng 种子 → 同种子同定调场同地形（MC 硬要求）。
* DDPM 反演 `strat=false`（DDIM 风格）无随机项；Rng 值语义纯函数。
* 边缘交叉淡化权重为解析函数（仅依赖连续条件草图），跨 tile 恒连续。

## 融合 / Fusion

```
elev = coarse_elev(x,z,seed)   ∈ [-1,1]
mtn  = coarse_mountain(x,z,seed) ∈ [0,1]
bed      = sea + elev·24
landMask = clamp(0.6+elev, 0, 1)
surface  = bed + 3 + landMask·(mtn·15 + hills_noise(x,z,seed)·5)
```

* 宏观（大陆/海陆/山带）由扩散定调；微观起伏（hills）与洞穴（四形态）保持纯噪声 → 速度不变。
* 缺省融合强度可配置（常量族），支持回退到纯噪声（恒等路径）以对照与验收。

## 验收 / Verification

* 训练 loss 单调下降；采样确定性（同种子逐位一致）；自包含 forward 与 std/nn forward 逐位一致。
* 整体性度量探针：海陆比例、最大连通大陆占比、海岸线连通、山带-海岸相关。
* DLL 冒烟：新导出符号查询、确定性、与旧 DLL 纯噪声路径对照（hills/caves 逐位不变，仅宏观被引导）。
* 既有探针（ddpm/nn/tensor 等）回归全绿；自举不动点校验。

## 交付 / Delivery

* tiec 仓（p.9.14.x，逐子项提交）：macro_gen / diffunet / trainer+权重导出 / sampler+度量探针。
* Subterra（_tmp/subterra-tie-core → subterra-engine 捆绑 DLL）：运行时模块 + 重建 subterra_density.dll + 冒烟。
* Java 桥零改动（融合全部在 DLL 内）；POI/低精度 LOD 后续可选复用 coarse 查询符号。
