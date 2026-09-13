# scripts/verify-cache.ps1 —— p.9.1.3 编译缓存验收脚本
# 用法（仓库根目录）: pwsh ./scripts/verify-cache.ps1 [-Tiec .\compiler\tiec.exe]
# 验收点：
#   1) 首次编译 = 未命中，入缓存（"已缓存编译产物"）
#   2) 再次同一输入/参数编译 = 缓存命中，跳过编译（"缓存命中"），产物一致
#   3) 篡改输入源码后编译 = 缓存键变，重编（不再"缓存命中"）
#   4) --no-cache 强制重编（不命中）
# 返回：全部通过输出 "CACHE-VERIFY OK"；任一步失败 exit 1。

param([string]$Tiec = ".\compiler\tiec.exe")

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# 用临时副本验证（不污染 examples/hello.tie）；缓存目录用缺省 ~/.tiec-cache
$probe = "$root\examples\_cache_probe.tie"
$out   = "$root\examples\_cache_probe.exe"
Copy-Item "$root\examples\hello.tie" $probe -Force

# 预清理该工程缓存条目与产物
$cache = "$HOME\.tiec-cache"
Get-ChildItem $cache -Filter "tc*.cache" -ErrorAction SilentlyContinue | Remove-Item -Force
Remove-Item $out -Force -ErrorAction SilentlyContinue

$fail = 0

# 1) 首次：未命中 → 入缓存
$r1 = & $Tiec $probe -o $out 2>&1 | Out-String
if ($r1 -match "已缓存编译产物") {
    Write-Host "[1] miss->cache OK"
} else {
    Write-Host "[1] MISS-SHOULD-CACHE FAIL"; $fail = 1
}

# 产物一致性的比对基准（第 2 次命中前后都应指向同一产物）
$h_base = (Get-FileHash $out -Algorithm SHA256).Hash

# 2) 再次：命中
$r2 = & $Tiec $probe -o $out 2>&1 | Out-String
if ($r2 -match "缓存命中") {
    Write-Host "[2] hit OK"
} else {
    Write-Host "[2] HIT-SHOULD-HIT FAIL"; $fail = 1
}
$h_hit = (Get-FileHash $out -Algorithm SHA256).Hash
if ($h_base -ne $h_hit) {
    Write-Host "[2] HIT-PRODUCT-DIVERGED FAIL"; $fail = 1
} else {
    Write-Host "[2] product-identical OK"
}

# 3) 篡改输入 → 缓存键变，重编（不命中）
"// tamper-$([guid]::NewGuid().ToString('N').Substring(0,8))" | Add-Content $probe
$r3 = & $Tiec $probe -o $out 2>&1 | Out-String
if ($r3 -match "缓存命中") {
    Write-Host "[3] TAMPER-SHOULD-RECOMPILE FAIL"; $fail = 1
} else {
    Write-Host "[3] tamper->recompile OK"
}

# 4) --no-cache：即使命中键存在也强制重编（不命中）
$r4 = & $Tiec $probe --no-cache -o $out 2>&1 | Out-String
if ($r4 -match "缓存命中") {
    Write-Host "[4] NOCACHE-SHOULD-RECOMPILE FAIL"; $fail = 1
} else {
    Write-Host "[4] --no-cache forces recompile OK"
}

Remove-Item $probe, $out -Force -ErrorAction SilentlyContinue

if ($fail -eq 0) {
    Write-Host "CACHE-VERIFY OK"
    exit 0
}
Write-Host "CACHE-VERIFY FAILED"
exit 1