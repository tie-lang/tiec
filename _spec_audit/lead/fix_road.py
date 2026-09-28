# -*- coding: utf-8 -*-
"""ROAD.md 记录更正落盘（2026-09-27）
依据：_spec_audit/out/records.md 的「确证不实（建议更正）」5 条。
只改实测确证的部分；保持 CRLF 与 UTF-8。
"""
import shutil

PATH = 'F:/Projects/tie-repo/tie-main/ROAD.md'
shutil.copyfile(PATH, PATH + '.bak_20260927')

raw = open(PATH, 'rb').read()
lines = raw.split(b'\n')

# 行号 -> (标记替换对或 None, 正文替换对或 None, 追加的更正措辞)
FIX = {
    414: (
        (b'- [ ] p.9.13.4', b'- [~] p.9.13.4'),
        None,
        '**记录更正 2026-09-27**：原标 `[ ]`（未落地）→ 实为**部分落地**，标记同步为 `[~]`；'
        '正文已如实写「部分落地 2026-09-26」但行首标记未回填（证据：`_spec_audit/records/p9/c134b.tie` '
        '实测七种箭头形态输出 `20 8 true 13 6 18 3` 全通过；commit 22b1519/9c8a3a7/1401cc1/1231058/4798cec 经 git log 核对真实）',
    ),
    417: (
        None,
        ('**临时单参函数 `f = t -> expr` 仍未落地'.encode('utf-8'),
         '**临时单参函数 `f = t -> expr` 在实参位与无初始化声明位仍未落地'.encode('utf-8')),
        '**记录更正 2026-09-27**：原记「`f = t -> expr` 仍未落地」不实——**声明位与赋值位已落地**'
        '（`var f: fn(i64) -> i64 = t -> t + 1` 与已初始化标注变量的 `f = t -> t + 1` 均实测可用，前者输出 2、后者 42；'
        'commit 2cec664）。真正未落的是**实参位**（`apply(t -> t * 3, 5)` 报 E00488）与**无初始化声明的赋值**（报 E00484）。'
        '本条与第 368 行 p.9.11.34 的表述应统一（证据：样例 `_spec_audit/records/p9/c34c_arrowassign.tie`、'
        '`c34e_argctx.tie`、`c34f_noinit.tie`）',
    ),
    419: (
        (b'- [ ] [~] p.9.13.5', b'- [~] p.9.13.5'),
        None,
        '**记录更正 2026-09-27**：原标记为 `[ ] [~]` **双标记（格式非法，机器不可解析）** → 更正为单一 `[~]`；'
        '最小内核已落地，与正文「最小内核已落地 2026-09-27」一致（证据：tlib `std/dataflow.tie` 350 行存在且行数与记录吻合；'
        '样例 `_spec_audit/records/p9/c135_df.tie` 实测链式图 10 → +1 输出 v=22；commit 818f9f3 经 git log 核对真实）',
    ),
    473: (
        (b'- [ ] p.9.17.3', b'- [~] p.9.17.3'),
        None,
        '**记录更正 2026-09-27**：原标 `[ ]`（未落地）→ 实为**前半落地**，标记同步为 `[~]`；'
        '正文自述「前半落地 2026-09-27，tiec 2f66430」而行首标记未回填（证据：commit 2f66430 '
        '「perf(interp): interned-id keys for the variable environment」经 git log 核对真实）',
    ),
    514: (
        (b'- [ ] p.9.20.3', b'- [x] p.9.20.3'),
        None,
        '**记录更正 2026-09-27**：原标 `[ ]`（未落地）→ 该子项**已落地**，标记同步为 `[x]`；'
        '正文白纸黑字写「已落地 2026-09-21，tiec b8a77f7」而行首标记未回填，且同族 p.9.20.2/.4/.5 均为 `[x]`。'
        '仅「每档性能参考」未补，该验收属 p.9.20.6（自身已单列）（证据：commit b8a77f7 '
        '「feat(middle): t1 intra-function passes」经 git log 核对真实；`tiec.exe --no-cache -t1` 可正常编译）',
    ),
}

for n, (mark, text_sub, note) in sorted(FIX.items()):
    ln = lines[n - 1]
    eol = b''
    if ln.endswith(b'\r'):
        ln, eol = ln[:-1], b'\r'
    if mark is not None:
        assert ln.count(mark[0]) == 1, (n, 'marker not unique', ln[:80])
        ln = ln.replace(mark[0], mark[1], 1)
    if text_sub is not None:
        assert ln.count(text_sub[0]) == 1, (n, 'text not unique', ln[:80])
        ln = ln.replace(text_sub[0], text_sub[1], 1)
    ln = ln + note.encode('utf-8')
    lines[n - 1] = ln + eol

open(PATH, 'wb').write(b'\n'.join(lines))
print('ROAD.md updated: 5 records corrected (414, 417, 419, 473, 514)')
