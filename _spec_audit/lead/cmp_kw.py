import re

# 规范 §1.6（ch01_lex.tie 中 dp.kvrow 的第二列）
spec_src = open('F:/Projects/tie-repo/tofflib/spec/ch01_lex.tie', encoding='utf-8').read()
blk = spec_src[spec_src.index('1.6  关键字'):spec_src.index('1.7  数值字面量')]
spec = []
for m in re.finditer(r'dp\.kvrow\("([^"]+)",\s*"([^"]+)"\)', blk):
    spec += m.group(2).split()
spec = set(spec)

# 编译器 build_kw()
csrc = open('F:/Projects/tie-repo/tiec/compiler/frontend/lex_symtab.tie', encoding='utf-8').read()
body = csrc[csrc.index('func build_kw()'):csrc.index('kw_keys = table_new_string()')]
impl = set(re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"', body.split('var v:')[0]))

print("规范 §1.6 关键字数 :", len(spec))
print("编译器 build_kw 数 :", len(impl))
print()
print("【规范有、实现无】", sorted(spec - impl) or "（无）")
print("【实现有、规范 §1.6 未列】", sorted(impl - spec) or "（无）")
print("【交集】", len(spec & impl))
