# scripts/fetch-lib.ps1 —— p.9.13.7-B 内置库零副本：拉取内置库根（tie-lang/tlib）
# ============================================================================
# 背景：内置库 std/ext/rdu/sys 已迁出 tiec 仓（零副本），由编译器按
#   --lib-root <dir> > TIE_LIB_ROOT 环境变量 > 默认 ~/.tiec-lib/tlib
# 解析到"内置库根"检出后经 /std /ext /rdu /sys 别名展开（compiler/frontend/semantic.tie
#   resolve_import_path 的 / 前缀分支 + expand_one_import 库根缺失诊断）。
# 前置：移植+自举/门禁前须先保证库根就位（本脚本），否则编译报
#   error[E00391]...内置库根缺失: '<lib-root>'（运行 scripts/fetch-lib.ps1 或设置
#   TIE_LIB_ROOT / --lib-root）。
# 用法：pwsh scripts/fetch-lib.ps1  [-Root <dir>]
#   -Root 缺省 = $env:TIE_LIB_ROOT 或默认 ~/.tiec-lib/tlib。
param([string]$Root)
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Root)) {
    if (-not [string]::IsNullOrWhiteSpace($env:TIE_LIB_ROOT)) { $Root = $env:TIE_LIB_ROOT }
    else { $Root = Join-Path $env:USERPROFILE ".tiec-lib\tlib" }
}

$LibOk = (Test-Path (Join-Path $Root 'std')) -and (Test-Path (Join-Path $Root 'ext')) `
       -and (Test-Path (Join-Path $Root 'rdu')) -and (Test-Path (Join-Path $Root 'sys'))
if ($LibOk) {
    Write-Host "[fetch-lib] 库根已就绪: $Root"
    exit 0
}

if (Test-Path (Join-Path $Root '.git')) {
    Write-Host "[fetch-lib] 存在检出但库目录不完整，请检查: $Root"
    exit 1
}

Write-Host "[fetch-lib] 克隆 tie-lang/tlib -> $Root"
$parent = Split-Path -Parent $Root
if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
git clone --depth 1 https://github.com/tie-lang/tlib.git $Root
if ($LASTEXITCODE -ne 0) { Write-Host "[fetch-lib] clone 失败"; exit 1 }

if (-not (Test-Path (Join-Path $Root 'std'))) { Write-Host "[fetch-lib] 拉取后仍缺 std，异常"; exit 1 }
Write-Host "[fetch-lib] 完成: $Root"
exit 0