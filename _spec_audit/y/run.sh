#!/bin/bash
# 用法: run.sh <probe.tie>  —— 编译并把日志写到 F:/Projects/_tmp/<name>.log
cd /f/Projects/tie-repo/tiec
n=$(basename "$1" .tie)
./compiler/tiec.exe "_spec_audit/y/$1" -l2 -t0 --no-warn --no-cache -o "F:/Projects/_tmp/$n.exe" > "F:/Projects/_tmp/$n.log" 2>&1
echo "rc=$? ($n)"
grep -E "error|成功|警告" "F:/Projects/_tmp/$n.log" | head -6
