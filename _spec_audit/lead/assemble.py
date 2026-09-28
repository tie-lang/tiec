# -*- coding: utf-8 -*-
"""汇编最终交付文档：head + ch03 + 各路章节表 + tail"""
import io, os

BASE = 'F:/Projects/tie-repo/tiec/_spec_audit'
OUT = 'F:/Projects/tie-repo/tiec/docs/2026-09-27-language-spec-implementation-audit.md'

def read(p):
    return io.open(p, encoding='utf-8').read()

def section(text, start_marker, end_markers):
    i = text.index(start_marker)
    j = len(text)
    for m in end_markers:
        k = text.find(m, i)
        if k != -1 and k < j:
            j = k
    return text[i:j].rstrip() + '\n'

head = read(BASE + '/lead/part_head.md')
ch03 = read(BASE + '/lead/part_ch03.md')
tail = read(BASE + '/lead/part_tail.md')

a = read(BASE + '/out/a.md')
ch0102 = section(a, '## 第 1 章', ['## 记录更正'])

b = read(BASE + '/out/b.md')
ch0405 = section(b, '## 第 4 章', ['## 记录更正'])

c = read(BASE + '/out/c.md')
ch0609 = section(c, '## 第 6 章', ['## 记录更正'])

d = read(BASE + '/out/d.md')
ch1013 = section(d, '## 第 10 章', ['## 记录更正'])

e = read(BASE + '/out/e.md')
ch1416 = section(e, '## 第 14 章', ['## 记录更正'])

parts = [head.rstrip(), ch0102, ch03, ch0405, ch0609, ch1013, ch1416, tail.lstrip()]
doc = '\n\n'.join(p.strip() + '\n' for p in parts)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, 'w', encoding='utf-8', newline='\n').write(doc)

print('written:', OUT)
print('lines:', doc.count('\n') + 1)
print('chars:', len(doc))
