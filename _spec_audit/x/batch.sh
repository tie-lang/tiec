#!/bin/bash
# 用法: batch.sh <文件...>  逐个编译，只输出 rc 与首条错误
cd /f/Projects/tie-repo/tiec || exit 9
for f in "$@"; do
  b=$(basename "$f" .tie)
  out="F:/Projects/_tmp/x_$b.log"
  ./compiler/tiec.exe "_spec_audit/x/$b.tie" -l2 -t0 --no-warn --no-cache -o "F:/Projects/_tmp/x_$b.exe" > "$out" 2>&1
  rc=$?
  e=$(grep -aE "error" "$out" | head -1)
  if [ $rc -eq 0 ]; then echo "OK   $b"; else echo "FAIL $b rc=$rc | $e"; fi
done
