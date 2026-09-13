# scripts/verify-crashdiag.ps1 —— p.9.2.1 崩溃诊断验收脚本
# 用法（仓库根目录）: pwsh ./scripts/verify-crashdiag.ps1
# 验收点：
#   1) 崩溃探针：crashdiag 应退出码 1，崩溃日志含符号化 backtrace
#      （main -> a -> b -> boom 调用链，含函数体行号）与错误消息
#   2) 正常探针：crashdiag 应退出码 0、控制台输出探针结果、不写崩溃日志
#   3) 自举不动点：tiec.exe 用自身编译自身 → tiec_new2，两次产物 SHA256 一致
# 返回：全部通过输出 "CRASHDIAG-VERIFY OK"；任一失败 exit 1。

param([string]$Tiec = ".\compiler\tiec.exe")

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$src = "$root\compiler\dbug\crashdiag.tie"
$exe = "$root\compiler\dbug\crashdiag.exe"
$probeCrash = "$root\compiler\dbug\_crash_probe.tie"
$probeOk    = "$root\compiler\dbug\_ok_probe.tie"
$logCrash = "$root\compiler\dbug\_crash_probe.crash.log"
$logOk    = "$root\compiler\dbug\_ok_probe.crash.log"

$fail = 0

# 0) 用当前 tiec 重新构建 crashdiag（保证产物来自当前编译器/仪器）
Write-Host "[0] 构建 crashdiag..."
& $Tiec $src -o $exe --no-cache | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "[0] CRASHDIAG-BUILD FAIL"; exit 1 }
Write-Host "[0] build OK"

Remove-Item $logCrash, $logOk -Force -ErrorAction SilentlyContinue

# 1) 崩溃路径
Write-Host "[1] 崩溃探针..."
& $exe -o $logCrash $probeCrash 2>&1 | Out-String | Write-Host
$c1 = $LASTEXITCODE
if ($c1 -ne 1) {
    Write-Host "[1] CRASH-EXITCODE FAIL (got $c1, want 1)"; $fail = 1
} elseif (-not (Test-Path $logCrash)) {
    Write-Host "[1] CRASH-LOG-NOT-WRITTEN FAIL"; $fail = 1
} else {
    $log = Get-Content $logCrash -Raw
    $ok = ($log -match "除零错误") -and ($log -match "调用栈") -and
          ($log -match "boom") -and ($log -match "\bb\b") -and ($log -match "\ba\b") -and ($log -match "main")
    if ($ok) {
        Write-Host "[1] crash+backtrace OK (main->a->b->boom)"
    } else {
        Write-Host "[1] BACKTRACE-CONTENT FAIL"; $fail = 1
    }
}

# 2) 正常路径
Write-Host "[2] 正常探针..."
$out2 = & $exe -o $logOk $probeOk 2>&1 | Out-String
$c2 = $LASTEXITCODE
if ($c2 -ne 0) {
    Write-Host "[2] OK-EXITCODE FAIL (got $c2, want 0)"; $fail = 1
} elseif ($out2 -notmatch "probe=42") {
    Write-Host "[2] OK-OUTPUT FAIL"; $fail = 1
} elseif (Test-Path $logOk) {
    Write-Host "[2] OK-SHOULD-NO-LOG FAIL"; $fail = 1
} else {
    Write-Host "[2] normal-exit OK (`"probe=42`", no log)"
}

# 3) 自举不动点（tiec.exe 编译自身，二次一致）
Write-Host "[3] 自举不动点..."
$tmp1 = "$root\compiler\tiec_fp1.exe"
$tmp2 = "$root\compiler\tiec_fp2.exe"
Remove-Item $tmp1, $tmp2 -Force -ErrorAction SilentlyContinue
& $Tiec "$root\compiler\driver.tie" -o $tmp1 --no-cache | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "[3] FP-STAGE1 FAIL"; $fail = 1 }
else {
    & $tmp1 "$root\compiler\driver.tie" -o $tmp2 --no-cache | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "[3] FP-STAGE2 FAIL"; $fail = 1 }
    else {
        $h1 = (Get-FileHash $tmp1 -Algorithm SHA256).Hash
        $h2 = (Get-FileHash $tmp2 -Algorithm SHA256).Hash
        if ($h1 -ne $h2) { Write-Host "[3] FIXPOINT-DIVERGE FAIL"; $fail = 1 }
        else { Write-Host "[3] fixpoint OK ($h1)" }
    }
}
Remove-Item $tmp1, $tmp2 -Force -ErrorAction SilentlyContinue

Remove-Item $logCrash, $logOk -Force -ErrorAction SilentlyContinue

if ($fail -eq 0) { Write-Host "CRASHDIAG-VERIFY OK"; exit 0 }
Write-Host "CRASHDIAG-VERIFY FAILED"; exit 1