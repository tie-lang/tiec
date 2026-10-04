#!/bin/bash
cd /f/Projects/tie-repo/tiec || exit 9
p="_spec_audit/x/$(basename "$1")"
b=$(basename "$1" .tie)
out="F:/Projects/_tmp/x_$b.log"
./compiler/tiec.exe "$p" -l2 -t0 --no-warn --no-cache -o "F:/Projects/_tmp/x_$b.exe" > "$out" 2>&1
rc=$?
echo "=== $b rc=$rc"
grep -aE "error" "$out" | head -8
