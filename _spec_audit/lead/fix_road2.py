# -*- coding: utf-8 -*-
"""ROAD.md 第 363 行（p.9.11.29）补充实现缺陷注记。
不改标记（交付物 doc 注册表 / pdoc_* / --dump-docs 三者确实存在），
只补充「--dump-docs 对含必需头部的文件不可用」这一实测确证的可用性缺陷。
"""
PATH = 'F:/Projects/tie-repo/tie-main/ROAD.md'
raw = open(PATH, 'rb').read()
lines = raw.split(b'\n')

n = 363
ln = lines[n - 1]
eol = b''
if ln.endswith(b'\r'):
    ln, eol = ln[:-1], b'\r'

note = (
    '**补充 2026-09-27（非改标记）**：上述三项交付物均存在，但 `--dump-docs` 的**入口有缺陷**——'
    '`driver.tie:262` 在处理 `--dump-docs` 时直接 `parser.parse_ast(src)`，**早于文件头部 `type tie<...>` 的剥离**，'
    '故对任何含规范 §1.1 所要求的头部（头部必须位于文件最前）的 tie 文件一律报 '
    '`error[E00000] @1:1: 顶层只允许函数定义、import、using、struct、enum、命名空间声明、extern 声明、全局变量或宏定义，实际是 标识符 \'type\'`，'
    '只能用于**无头部**文件。实测：含头部的 `d1.tie` 失败、去掉头部的 `d2.tie` 正常输出 '
    '`共 1 条声明 doc:  [2] add: 计算两数之和`。即 doc 注册表本身工作正常，坏的是 `--dump-docs` 这条读取路径。'
).encode('utf-8')

if b'\xe8\xa1\xa5\xe5\x85\x85 2026-09-27' in ln:
    print('already annotated, skip')
else:
    lines[n - 1] = ln + note + eol
    open(PATH, 'wb').write(b'\n'.join(lines))
    print('ROAD.md line 363 annotated (defect note, marker unchanged)')
