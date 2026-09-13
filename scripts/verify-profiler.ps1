# scripts/verify-profiler.ps1 —— p.9.2.4 剖析器验收脚本
# 用法（仓库根目录）: pwsh ./scripts/verify-profiler.ps1
# 验收点：
#   1) profiler 探针运行成功（退出码 0）
#   2) 每函数：fib 调用次数 > hot（递归热点频率体现），均含 main
#   3) 折叠栈含 "main;hot" 与 "main;fib;fib"
#   4) 文本火焰图含主路径
# 全部通过输出 "PROFILER-VERIFY OK"；任一步失败 exit 1。

param([string]$Tiec = ".\compiler\tiec.exe")

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$src = "$root\compiler\dbug\profiler.tie"
$exe = "$root\compiler\dbug\profiler.exe"
$probe = "$root\compiler\dbug\_prof_probe.tie"
$out = "$env:TEMP\profiler_verify.out"

$fail = 0

Write-Host "[0] 构建 profiler..."
& $Tiec $src -o $exe --no-cache | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "[0] PROFILER-BUILD FAIL"; exit 1 }
Write-Host "[0] build OK"

Remove-Item $out -Force -ErrorAction SilentlyContinue
& $exe -o $out $probe | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "[1] PROFILER-RUN FAIL"; $fail = 1 }
else { Write-Host "[1] profiler run OK" }

$rep = Get-Content $out -Raw
if ($rep -notmatch "剖析器") { Write-Host "[1b] REPORT-HEADER FAIL"; $fail = 1 }

# 2) 每函数汇总
$hasMain = $rep -match "(?m)^main\t"
$hasFib  = $rep -match "(?m)^fib\t\d+\t"
$hasHot  = $rep -match "(?m)^hot\t\d+\t"
if ($hasMain -and $hasFib -and $hasHot) {
    Write-Host "[2] per-function rows (main/fib/hot) OK"
} else {
    Write-Host "[2] PER-FUNCTION FAIL"; $fail = 1
}
# fib 调用次数 > hot（递归热点）
$fibN = -1; $hotN = -1
if ($rep -match "(?m)^fib\t(\d+)\t") { $fibN = [int]$Matches[1] }
if ($rep -match "(?m)^hot\t(\d+)\t") { $hotN = [int]$Matches[1] }
if ($fibN -gt $hotN) { Write-Host "[2b] fib-calls($fibN) > hot($hotN) OK" }
else { Write-Host "[2b] FIB-HOT-COUNT FAIL (fib=$fibN hot=$hotN)"; $fail = 1 }

# 3) 折叠栈
if ($rep -match "main;hot" -and $rep -match "main;fib;fib") {
    Write-Host "[3] folded stacks (main;hot / main;fib;fib) OK"
} else {
    Write-Host "[3] FOLDED-STACKS FAIL"; $fail = 1
}

# 4) 火焰图
if ($rep -match "火焰图") {
    Write-Host "[4] flame graph section OK"
} else {
    Write-Host "[4] FLAME-GRAPH FAIL"; $fail = 1
}

Remove-Item $out -Force -ErrorAction SilentlyContinue

if ($fail -eq 0) { Write-Host "PROFILER-VERIFY OK"; exit 0 }
Write-Host "PROFILER-VERIFY FAILED"; exit 1