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

# ==================== (E)(F)(G) lock 凭据域（r.1.6.7 去锁语法） ====================
# 与上面的「自动独占」不变量并列：这里断言的是**显式凭据路径**（语法层去锁）。
# 用词区分：「凭据去锁」= 显式凭据路径；「独占免锁」= 编译器自动证明路径。
LOCKS="$OUT/lock_audit.txt"
"$TIEC" tests/language/lock_credential.tie --esc-audit --no-cache --no-warn \
  -o "$OUT/lock_cred.exe" 2>&1 | grep -E '^\[esc\].*凭据去锁' > "$LOCKS"

lk_absent() {
  if grep -q "$1" "$LOCKS"; then
    echo "FAIL 不应去锁却去锁: $2"
    grep "$1" "$LOCKS" | head -3 | sed 's/^/       /'
    fail=1
  else
    echo "PASS 未去锁: $2"
  fi
}
lk_present() {
  if grep -q "$1" "$LOCKS"; then
    echo "PASS 已去锁: $2"
  else
    echo "FAIL 应去锁却未去锁: $2"
    fail=1
  fi
}

echo "== (E) lock 域：三种持证形态必须去锁 =="
lk_present '函数=ok_block_lock'   '块级 unsafe with(lock)'
lk_present '函数=ok_use_lock'     '块级绑证 unsafe use g（g: guard<lock>）'
lk_present '函数=ok_fn_lock'      '函数级 #[unsafe.lock]'

echo "== (F) lock 域：负例必须**不**去锁 =="
lk_absent '函数=no_wrong_domain'    '错域凭据（guard<share>）⇒ 域隔离'
lk_absent '函数=no_credential'      '无凭据（仅 unsafe 上下文）⇒ 双锁之锁二'
lk_absent '函数=no_closure_inherit' '闭包体不继承外层凭据（防 spawn 后竞态）'

echo "== (G) 文件级授权：范围必须精确限定在本文件 =="
"$TIEC" tests/language/lock_file_auth.tie --esc-audit --keep-ir --no-cache --no-warn \
  -o "$OUT/lock_file.exe" 2>&1 | grep -E '^\[esc\].*凭据去锁' > "$OUT/file_audit.txt"
if grep -q '函数=file_auth_fn' "$OUT/file_audit.txt"; then
  echo "PASS 已去锁: 主文件函数（文件级 unsafe:lock 授权）"
else
  echo "FAIL 应去锁却未去锁: 主文件函数"; fail=1
fi
# import 的模块**必须仍加锁**：直接查 IR 的调用形态
IRF=$(ls -t "$OUT"/lock_file*.opt.ll 2>/dev/null | head -1)
if [ -n "$IRF" ]; then
  if awk '/^define .*push_it"/,/^}/' "$IRF" | grep -q '"tl_tbl\$tbl_push"'; then
    echo "PASS 仍加锁: import 模块函数（文件级授权不波及 import）"
  else
    echo "FAIL import 模块函数被误去锁（范围失控）"; fail=1
  fi
  if awk '/^define .*@file_auth_fn/,/^}/' "$IRF" | grep -q 'tbl_push_nl'; then
    echo "PASS 去锁: 主文件函数 IR 走免锁入口"
  else
    echo "FAIL 主文件函数 IR 未走免锁入口"; fail=1
  fi
else
  echo "FAIL 未取到文件级探针的 IR"; fail=1
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "=== esc 安全不变量: PASS（审计 $(wc -l < "$AUDIT") 条，零违规）==="
  exit 0
fi
echo "=== esc 安全不变量: FAIL ==="
echo "（审计全文保留在 $AUDIT）"
exit 1
