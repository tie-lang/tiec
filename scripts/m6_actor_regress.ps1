$env:TIE_TRM_LITE_LIB = "F:\Projects\tie-repo\trm-lite\trm_lite.a"
Set-Location "F:\Projects\tie-repo\tiec"
$tiec = "F:\Projects\tie-repo\tiec\compiler\tiec_new.exe"
$files = Get-ChildItem "tests\m6_actor\*.tie" | Sort-Object Name
$pass = 0; $fail = 0
$outdir = "F:\Projects\tie-repo\tiec\_m6_out"
New-Item -ItemType Directory -Force $outdir | Out-Null
foreach ($f in $files) {
    $base = $f.BaseName
    $isNeg = $base -like "*_neg_*"
    $exe = Join-Path $outdir ($base + ".exe")
    $log = Join-Path $outdir ($base + ".log")
    # compile
    $c = & $tiec $f.FullName -o $exe --no-cache 2>&1
    $crc = $LASTEXITCODE
    if ($isNeg) {
        # negative: compile must fail
        if ($crc -ne 0) {
            Write-Output "PASS(neg-compile-reject) $base"
            $pass++
        } else {
            Write-Output "FAIL(neg-compiled-ok) $base"
            $fail++
        }
        continue
    }
    if ($crc -ne 0) {
        Write-Output "FAIL(compile) $base : $($c | Select-Object -First 3)"
        $fail++
        continue
    }
    # run
    $out = & $exe 2>&1 | Out-String
    $rc = $LASTEXITCODE
    # panic_raise expects nonzero exit + raise message; others expect 通过/PASS and rc 0
    if ($base -eq "actor_a4_panic_raise") {
        if ($rc -ne 0 -and ($out.Contains("actor 方法 panic") -or $out.Contains("bomb!"))) {
            Write-Output "PASS(run-raise) $base"
            $pass++
        } else {
            Write-Output "FAIL(run-raise) $base rc=$rc out=$out"
            $fail++
        }
        continue
    }
    $failStr = [string][char]0x5931 + [char]0x8D25  # 失败
    if ($rc -eq 0 -and -not $out.Contains($failStr) -and $out.Trim().Length -gt 0) {
        Write-Output "PASS(run) $base"
        $pass++
    } else {
        Write-Output "FAIL(run) $base rc=$rc out=$($out.Substring(0, [Math]::Min(200, $out.Length)))"
        $fail++
    }
}
Write-Output "===== m6_actor: PASS=$pass FAIL=$fail ====="
