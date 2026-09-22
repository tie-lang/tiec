#!/bin/sh
# 自举不动点校验：tiec(入库) → n1 → n2 → n3，SHA(n2)==SHA(n3) 即不动点
# 用法：sh tools/fp.sh [输出目录]     输出目录默认落在仓库外侧的 ../_tiec_verify/fp，避免污染工作树
set -u
ROOT=${TIEC_ROOT:-$(pwd)}
cd "$ROOT" || exit 1
OUT=${1:-../_tiec_verify/fp}
mkdir -p "$OUT"
S=.  # 源码根 = 仓库根
FLAGS="-l2 -t0 --no-warn --no-cache"

echo "[1/4] 入库 tiec 编译 driver … $(date +%T)"
./compiler/tiec.exe compiler/driver.tie $FLAGS -o "$OUT/n1.exe" || exit 1
echo "[2/4] n1 自编 … $(date +%T)"
"$OUT/n1.exe" compiler/driver.tie $FLAGS -o "$OUT/n2.exe" || exit 1
echo "[3/4] n2 自编 … $(date +%T)"
"$OUT/n2.exe" compiler/driver.tie $FLAGS -o "$OUT/n3.exe" || exit 1
echo "[4/4] 比对 … $(date +%T)"
A=$(sha256sum "$OUT/n2.exe" | cut -c1-16)
B=$(sha256sum "$OUT/n3.exe" | cut -c1-16)
echo "n2=$A"
echo "n3=$B"
if [ "$A" = "$B" ]; then
    echo "FIXED-POINT OK ($A)"
    exit 0
fi
echo "FIXED-POINT MISMATCH"
exit 1
