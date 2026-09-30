#!/usr/bin/env bash
# _tiec_verify/esc_safety.sh —— r.1.6.7 编译期独占免锁的**安全不变量**门禁
# ---------------------------------------------------------------------------
# 用法: sh _tiec_verify/esc_safety.sh [<tiec.exe>]
#
# 用 --esc-audit 编译 tests/language/esc_safety.tie，核对：
#   (A) 审计输出**不得**出现任何 `g_` 前缀变量（全局表可被任意线程经名字触及）
#   (B) 审计输出**不得**出现函数形参名（所有权在调用方）
#   (C) 下列形态**不得**出现：pass_tbl / capture_tbl / store_into 的 inner /
#       loop_leak / global_refresh（这些点的句柄**已经**离开本次调用）
#   (D) 下列形态**必须**出现：ok_push / ok_read / ok_write / ok_literal /
#       ok_for_iter / ok_before_leak / ret_tbl 的 push
#       （ret_tbl 的 push 在 return **之前**，泄漏发生在 return 那一刻 ⇒ 允许）
#
# 这是「不会漏锁」这一核心安全性质的回归护栏：一旦判据被放宽到能把全局、形参或
# 已泄漏变量判为独占，本脚本立即失败。**宁可不优化，也绝不能漏锁。**
set -u
cd "$(dirname "$0")/.."
TIEC="${1:-compiler/tiec.exe}"
SRC="tests/language/esc_safety.tie"
OUT="_tiec_verify/esc_safety_out"
mkdir -p "$OUT"
AUDIT="$OUT/audit.txt"

"$TIEC" "$SRC" --esc-audit --no-cache --no-warn -o "$OUT/esc_safety.exe" 2>&1 \
  | grep -E '^\[esc\]' > "$AUDIT"

fail=0
chk_absent() { # $1=模式 $2=说明
  if grep -q "$1" "$AUDIT"; then
    echo "FAIL 不应出现却出现: $2"
    grep "$1" "$AUDIT" | head -3 | sed 's/^/       /'
    fail=1
  else
    echo "PASS 未出现: $2"
  fi
}
chk_present() { # $1=模式 $2=说明
  if grep -q "$1" "$AUDIT"; then
    echo "PASS 已出现: $2"
  else
    echo "FAIL 应出现却缺失: $2"
    fail=1
  fi
}

echo "== (A) 全局变量不得进快路径 =="
chk_absent '变量=g_' '全局表（g_ 前缀）'

echo "== (B) 函数形参不得进快路径 =="
chk_absent '函数=param_tbl.*变量=t' '形参表 t（param_tbl）'

echo "== (C) 已泄漏变量不得进快路径 =="
chk_absent '函数=pass_tbl.*行=.*' '传给用户函数后仍命中（pass_tbl）'
chk_absent '函数=capture_tbl.*table_push' '闭包捕获后仍命中（capture_tbl）'
chk_absent '函数=store_into.*变量=inner' '存入容器后仍命中（store_into 的 inner）'
chk_absent '函数=loop_leak'    '循环体内泄漏后整循环仍命中（loop_leak）'
chk_absent '函数=global_refresh' '全局重新赋新鲜初值后仍命中（global_refresh）'

echo "== (D) 可证独占必须进快路径 =="
chk_present '函数=ok_push'        'ok_push'
chk_present '函数=ok_read'        'ok_read'
chk_present '函数=ok_write'       'ok_write'
chk_present '函数=ok_literal'     'ok_literal'
chk_present '函数=ok_for_iter'    'ok_for_iter'
chk_present '函数=ok_before_leak' 'ok_before_leak（流敏感：泄漏点之前仍命中）'

chk_present '函数=ret_tbl'        'ret_tbl 的 push（泄漏在 return 那一刻，push 在其之前）'

echo
if [ "$fail" -eq 0 ]; then
  echo "=== esc 安全不变量: PASS（审计 $(wc -l < "$AUDIT") 条，零违规）==="
  exit 0
fi
echo "=== esc 安全不变量: FAIL ==="
echo "（审计全文保留在 $AUDIT）"
exit 1
