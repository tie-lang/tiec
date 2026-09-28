#!/bin/bash
# 批量实测：编译（+运行）给定 .tie 清单，输出 OK/FAIL 与错误码
# 用法: bash run.sh <file1.tie> [file2.tie ...]
TIEC=/f/Projects/tie-repo/tiec/compiler/tiec.exe
OUT=/f/Projects/tie-repo/tiec/_spec_audit/records/_bin
mkdir -p "$OUT"
for f in "$@"; do
  [ -f "$f" ] || { echo "MISSING  $f"; continue; }
  base=$(basename "$f" .tie)
  err=$("$TIEC" --no-cache "$f" -o "$OUT/$base.exe" 2>&1)
  if echo "$err" | grep -q "编译成功"; then
    # 尝试运行（有 main 才会产出 exe 并运行）
    if [ -f "$OUT/$base.exe" ]; then
      runout=$("$OUT/$base.exe" 2>&1)
      rc=$?
      printf 'OK(rc=%s)  %-40s | %s\n' "$rc" "$base" "$(echo "$runout" | tr '\n' ' ' | cut -c1-90)"
    else
      printf 'COMPILED-NOEXE %-32s\n' "$base"
    fi
  else
    code=$(echo "$err" | grep -o 'error\[E[0-9]*\]' | head -1)
    msg=$(echo "$err" | grep -o 'error\[E[0-9]*\][^"]*' | head -1 | cut -c1-80)
    printf 'FAIL      %-40s | %s %s\n' "$base" "$code" "$msg"
  fi
done
