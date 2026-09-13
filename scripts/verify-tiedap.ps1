# scripts/verify-tiedap.ps1 —— p.9.2.3 DAP 调试适配器验收脚本
# 用法（仓库根目录）: pwsh ./scripts/verify-tiedap.ps1
# 在 stdin 上按 Content-Length 帧模拟 DAP 客户端，驱动 tiedap.exe，验证：
#   initialize -> initialized 事件；setBreakpoints；launch；configurationDone -> stopped；
#   stackTrace（含 compute/main 帧）；variables（Global 含 g_count/g_msg）；
#   continue -> terminated；disconnect。
# 全部通过输出 "TIEDAP-VERIFY OK"；任一步失败 exit 1。

param([string]$Tiec = ".\compiler\tiec.exe")

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$src = Join-Path $root "compiler\dbug\tiedap.tie"
$exe = Join-Path $root "compiler\dbug\tiedap.exe"
$probe = Join-Path $root "compiler\dbug\_dap_probe.tie"
$probeEsc = $probe.Replace('\','/')

$fail = 0

# 0) 构建 tiedap
Write-Host "[0] 构建 tiedap..."
& $Tiec $src -o $exe --no-cache | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "[0] TIEDAP-BUILD FAIL"; exit 1 }
Write-Host "[0] build OK"

# DAP 帧工具：JSON -> 输入帧
function New-Frame([string]$json) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    return "Content-Length: $($bytes.Length)`r`n`r`n" + $json
}
# 解析输出流（多个 Content-Length 帧）为 message 数组。
# 注意：帧体可为非 ASCII（UTF-8），Content-Length 是**字节**长度；Parse 必须
# 在字节数组上按字节定位，不能用 .NET 字符串的字符下标（否则中文内容错位）。
function IndexOf-Bytes($hay, $need, $from) {
    for ($i = $from; $i -le $hay.Length - $need.Length; $i++) {
        $match = $true
        for ($j = 0; $j -lt $need.Length; $j++) {
            if ($hay[$i + $j] -ne $need[$j]) { $match = $false; break }
        }
        if ($match) { return $i }
    }
    return -1
}
function Parse-Frames([string]$raw) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($raw)
    $delim = [System.Text.Encoding]::UTF8.GetBytes("`r`n`r`n")
    $msgs = New-Object System.Collections.Generic.List[string]
    $pos = 0
    while ($true) {
        $hIdx = IndexOf-Bytes $bytes $delim $pos
        if ($hIdx -lt 0) { break }
        $hdr = [System.Text.Encoding]::ASCII.GetString($bytes, $pos, $hIdx - $pos)
        $m = [regex]::Match($hdr, 'Content-Length:\s*(\d+)')
        if (-not $m.Success) { break }
        $clen = [int]$m.Groups[1].Value
        $bodyStart = $hIdx + 4
        if ($bodyStart + $clen -gt $bytes.Length) { break }
        $body = [System.Text.Encoding]::UTF8.GetString($bytes, $bodyStart, $clen)
        $msgs.Add($body)
        $pos = $bodyStart + $clen
    }
    return $msgs
}

# 组装请求序列
$reqs = New-Object System.Collections.Generic.List[string]
$null = $reqs.Add((New-Frame '{"seq":1,"type":"request","command":"initialize","arguments":{}}'))
$null = $reqs.Add((New-Frame ('{"seq":2,"type":"request","command":"setBreakpoints","arguments":{"source":{"path":"' + $probeEsc + '"},"breakpoints":[{"line":11}]}}')))
$null = $reqs.Add((New-Frame ('{"seq":3,"type":"request","command":"launch","arguments":{"type":"tie","request":"launch","program":"' + $probeEsc + '"}}')))
$null = $reqs.Add((New-Frame '{"seq":4,"type":"request","command":"configurationDone","arguments":{}}'))
$null = $reqs.Add((New-Frame '{"seq":5,"type":"request","command":"stackTrace","arguments":{"threadId":1}}'))
$null = $reqs.Add((New-Frame '{"seq":6,"type":"request","command":"variables","arguments":{"variablesReference":1}}'))
$null = $reqs.Add((New-Frame '{"seq":7,"type":"request","command":"continue","arguments":{"threadId":1}}'))
$null = $reqs.Add((New-Frame '{"seq":8,"type":"request","command":"disconnect","arguments":{}}'))

$ps = New-Object System.Diagnostics.Process
$psi = New-Object System.Diagnostics.ProcessStartInfo($exe)
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.CreateNoWindow = $true
$ps.StartInfo = $psi
[void]$ps.Start()
foreach ($r in $reqs) { $ps.StandardInput.Write($r) }
$ps.StandardInput.Close()
$out = $ps.StandardOutput.ReadToEnd()
if (-not $ps.WaitForExit(10000)) { $ps.Kill() }
$msgs = Parse-Frames $out
Write-Host "[1] 收到 $($msgs.Count) 条消息"

# --- 断言 ---
# 1) 第 0 条应为 initialize 响应；第 1 条应为 initialized 事件
if ($msgs.Count -lt 8) { Write-Host "[1] TOO-FEW-MESSAGES FAIL"; $fail = 1 }
else {
    if ($msgs[0] -notmatch '"command":"initialize"' -or $msgs[0] -notmatch '"success":true') {
        Write-Host "[1a] INIT-RESPONSE FAIL"; $fail = 1
    } else { Write-Host "[1a] initialize response OK" }
    if ($msgs[1] -notmatch '"event":"initialized"') {
        Write-Host "[1b] INITIALIZED-EVENT FAIL"; $fail = 1
    } else { Write-Host "[1b] initialized event OK" }

    # 找 configurationDone 后的 stopped 事件
    $iStop = -1
    for ($i=0; $i -lt $msgs.Count; $i++) { if ($msgs[$i] -match '"event":"stopped"') { $iStop = $i; break } }
    if ($iStop -lt 0) { Write-Host "[2] NO-STOPPED-EVENT FAIL"; $fail = 1 }
    else { Write-Host "[2] stopped event OK (at cursor breakpoint)"; Write-Host "    " $msgs[$iStop] }

    # stackTrace 响应（configurationDone 响应之后第一条 stackTrace 响应）
    $iStack = -1
    for ($i=0; $i -lt $msgs.Count; $i++) { if ($msgs[$i] -match '"command":"stackTrace"') { $iStack = $i; break } }
    if ($iStack -lt 0) { Write-Host "[3] NO-STACKTRACE FAIL"; $fail = 1 }
    else {
        $frameOk = ($msgs[$iStack] -match '"compute"') -and ($msgs[$iStack] -match '"main"')
        if ($frameOk) { Write-Host "[3] stackTrace frames (compute/main) OK" }
        else { Write-Host "[3] STACKTRACE-FRAMES FAIL: " $msgs[$iStack]; $fail = 1 }
    }

    # variables 响应
    $iVar = -1
    for ($i=0; $i -lt $msgs.Count; $i++) { if ($msgs[$i] -match '"command":"variables"') { $iVar = $i; break } }
    if ($iVar -lt 0) { Write-Host "[4] NO-VARIABLES FAIL"; $fail = 1 }
    else {
        $varOk = ($msgs[$iVar] -match '"g_count"') -and ($msgs[$iVar] -match '"g_msg"')
        if ($varOk) { Write-Host "[4] variables (g_count/g_msg) OK" }
        else { Write-Host "[4] VARIABLES-GLOBALS FAIL: " $msgs[$iVar]; $fail = 1 }
    }

    # continue -> terminated 事件
    $iTerm = -1
    for ($i=0; $i -lt $msgs.Count; $i++) { if ($msgs[$i] -match '"event":"terminated"') { $iTerm = $i; break } }
    if ($iTerm -lt 0) { Write-Host "[5] NO-TERMINATED FAIL"; $fail = 1 }
    else { Write-Host "[5] continue -> terminated OK" }
}

if ($fail -eq 0) { Write-Host "TIEDAP-VERIFY OK"; exit 0 }
Write-Host "TIEDAP-VERIFY FAILED"; exit 1