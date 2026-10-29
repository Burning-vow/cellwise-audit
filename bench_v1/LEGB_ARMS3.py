"""腿 B 三臂（DeepSeek flash / 本地 Coder-7B / 本地 Qwen3-8B）判定侧对照。

为什么要单独一个脚本：7B 那臂的"能跑出读数只有 N 件"如果不拆成
①语法坏 ②跑完但没吐契约 JSON ③代码自己报错 ④我给的预览超时
四件事，就会被读成"7B 不行"。而 8B 那臂只生成了前 5 件，分母根本不是 192，
必须单独列，不许和另外两臂同表比"率"。

口径纪律：两臂的判定都是 rejudge_existing.py 的 420s / R=10 / horizon=40000，
所以这里比的是**判定后**的数，不是生成侧 run_note 的数（生成侧两臂预览超时不一致）。
"""
import io
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = io.open(os.path.join(HERE, 'LEGB_ARMS3.md'), 'w', encoding='utf-8')

ARMS = [
    ('flash (DeepSeek)', '_rejudge_flash20261018_v2.txt'),
    ('Coder-7B (本地)', '_rejudge_coder7b20261018.txt'),
    ('Qwen3-8B (本地)', '_rejudge_qwen8b20261018.txt'),
]

# 三门槛（10-17 定案，10-18 沿用）：低于任一门槛就说明这个端撑不起谱，要换端
GATES = [('可编译', 0.80), ('字段齐全', 0.60), ('参照可比率(格级)', 0.10)]


def w(s=''):
    OUT.write(s + '\n')


def load(p):
    recs = []
    with io.open(p, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('{'):
                recs.append(json.loads(line))
    return recs


def pct(a, b):
    return '—' if not b else '%.1f%%' % (100.0 * a / b)


def stats(recs):
    n = len(recs)
    kinds = defaultdict(int)
    for r in recs:
        kinds[r.get('kind') or '?'] += 1
    compilable = n - kinds['SYNTAX']
    # 有契约出口 = 跑完且吐出 JSON 行（NO_ENTRY/CRASH/SYNTAX 都没有可用出口）
    entered = sum(1 for r in recs if r.get('has_entry'))
    ok = kinds['OK']
    complete = sum(1 for r in recs if r.get('has_obs') and not r.get('missing_fields'))
    cell_in = sum(int(r.get('n_in') or 0) for r in recs)
    cell_tot = sum(int(r.get('n_tot') or 0) for r in recs)
    item_all = sum(1 for r in recs
                   if r.get('has_obs') and int(r.get('n_tot') or 0) > 0
                   and int(r.get('n_in') or 0) == int(r.get('n_tot') or 0))
    item_with_cells = sum(1 for r in recs if int(r.get('n_tot') or 0) > 0)
    return {
        'n': n, 'kinds': dict(kinds), 'compilable': compilable, 'entered': entered,
        'ok': ok, 'complete': complete, 'cell_in': cell_in, 'cell_tot': cell_tot,
        'item_all': item_all, 'item_with_cells': item_with_cells,
    }


def by_template(recs):
    d = defaultdict(list)
    for r in recs:
        d[r.get('template') or '?'].append(r)
    rows = []
    for tpl in sorted(d):
        rs = d[tpl]
        s = stats(rs)
        rows.append((tpl, s['n'], s['compilable'], s['entered'], s['cell_in'], s['cell_tot']))
    return rows


def main():
    w('# 腿 B 三臂判定侧对照（生成于 `LEGB_ARMS3.py`，口径 420s / R=10 / horizon=40000）\n')
    data = {}
    missing = []
    for name, fn in ARMS:
        p = os.path.join(HERE, fn)
        if os.path.exists(p):
            data[name] = load(p)
        else:
            missing.append((name, fn))

    w('## 1. 总表（分母都是 len() 现算）\n')
    w('| 臂 | 件数 | 可编译 | 有契约出口 | 判分件(OK) | 字段齐全 | 格级一致 | 件级全对 |')
    w('|---|---|---|---|---|---|---|---|')
    for name, _ in ARMS:
        if name not in data:
            w('| %s | — | 盘上无此文件：%s | | | | | |' % (name, _))
            continue
        s = stats(data[name])
        w('| %s | %d | %d (%s) | %d (%s) | %d | %d (%s) | %d/%d (%s) | %d/%d (%s) |' % (
            name, s['n'], s['compilable'], pct(s['compilable'], s['n']),
            s['entered'], pct(s['entered'], s['n']), s['ok'],
            s['complete'], pct(s['complete'], s['n']),
            s['cell_in'], s['cell_tot'], pct(s['cell_in'], s['cell_tot']),
            s['item_all'], s['item_with_cells'], pct(s['item_all'], s['item_with_cells'])))
    w('')

    w('## 2. 失败原因拆开（这一步不做，"能跑率低"就会被误读成"模型差"）\n')
    w('| 臂 | SYNTAX(语法坏) | NO_ENTRY(跑完没吐 JSON) | CRASH(代码自己报错) | OK | 其他 |')
    w('|---|---|---|---|---|---|')
    for name, _ in ARMS:
        if name not in data:
            continue
        s = stats(data[name])
        k = s['kinds']
        other = s['n'] - sum(v for kk, v in k.items()
                             if kk in ('SYNTAX', 'NO_ENTRY', 'CRASH', 'OK'))
        w('| %s | %d | %d | %d | %d | %d |' % (
            name, k.get('SYNTAX', 0), k.get('NO_ENTRY', 0), k.get('CRASH', 0),
            k.get('OK', 0), other))
    w('')

    w('## 3. 三门槛判定（n<100 的臂不参与，只列件数）\n')
    for name, _ in ARMS:
        if name not in data:
            continue
        s = stats(data[name])
        if s['n'] < 100:
            w('- **%s**：n=%d < 100 ⇒ **不进门槛判定**（分母不是 192，比"率"无意义）。' % (name, s['n']))
            continue
        vals = [s['compilable'] / s['n'],
                s['complete'] / s['n'],
                (s['cell_in'] / s['cell_tot']) if s['cell_tot'] else 0.0]
        parts = []
        verdict = []
        for (gname, gmin), v in zip(GATES, vals):
            parts.append('%s %.1f%%(门槛 %.0f%%,%s)' % (gname, 100 * v, 100 * gmin, '过' if v >= gmin else '不过'))
            verdict.append('过' if v >= gmin else '不过')
        w('- **%s**：%s ⇒ %s' % (name, '；'.join(parts), '全过' if all(x == '过' for x in verdict) else '有不过'))
    w('')

    w('## 4. 按题族拆（"闭式题 vs 事件驱动题"的分化是不是在两臂都出现）\n')
    closed = {'eoq', 'newsvendor'}
    for name, _ in ARMS:
        if name not in data:
            continue
        rs = data[name]
        if len(rs) < 100:
            continue
        rows = by_template(rs)
        w('### %s\n' % name)
        w('| 题族 | 件数 | 可编译 | 有出口 | 格级一致 | 属 |')
        w('|---|---|---|---|---|---|')
        for tpl, n, comp, ent, cin, ctot in rows:
            w('| %s | %d | %d | %d | %d/%d (%s) | %s |' % (
                tpl, n, comp, ent, cin, ctot, pct(cin, ctot),
                '闭式' if tpl in closed else '事件驱动'))
        cl = [r for r in rows if r[0] in closed]
        ev = [r for r in rows if r[0] not in closed]
        c_in, c_tot = sum(r[4] for r in cl), sum(r[5] for r in cl)
        e_in, e_tot = sum(r[4] for r in ev), sum(r[5] for r in ev)
        w('')
        w('- 小结：**闭式 %d/%d (%s) vs 事件驱动 %d/%d (%s)**\n' % (
            c_in, c_tot, pct(c_in, c_tot), e_in, e_tot, pct(e_in, e_tot)))

    w('## 5. CRASH 的异常类型分布（"能跑率低"到底是谁的错）\n')
    w('| 臂 | 异常型 | 件数 | 占该臂 CRASH |')
    w('|---|---|---|---|')
    for name, _ in ARMS:
        if name not in data or len(data[name]) < 100:
            continue
        exc = defaultdict(int)
        for r in data[name]:
            if r.get('kind') != 'CRASH':
                continue
            note = str(r.get('run_note') or '')
            if 'timed out' in note.lower():
                # 420s 还没跑完：这是"这件工件在 R=10/40000 下算不动"，不是我的预览超时
                exc['TIMEOUT(420s 未跑完)'] += 1
                continue
            found = re.findall(r'([A-Z][A-Za-z]*(?:Error|Exception))\b', note)
            # MemoryError 后面没有冒号（Python 就这么印），只匹配 `Error:` 会把它漏成"未识别"
            exc[found[-1] if found else '未识别'] += 1
        tot_cr = sum(exc.values())
        for k, v in sorted(exc.items(), key=lambda kv: -kv[1]):
            w('| %s | %s | %d | %s |' % (name, k, v, pct(v, tot_cr)))
        nonterm = exc['TIMEOUT(420s 未跑完)'] + exc['MemoryError']
        w('\n- **%s**：跑不完这一族（420s 未结束 + MemoryError）= **%d/%d 件（%s）**。'
          '这类不是"算错了"，是"**根本没给出答案**"⇒ 判分器对它们无从判起。\n'
          % (name, nonterm, sum(1 for _ in data[name]), pct(nonterm, len(data[name]))))
        for k in sorted(exc, key=lambda kv: -exc[kv]):
            if k == '未识别' and exc[k]:
                w('- ⚠ 还有 %d 件异常型未识别，**必须人读到行级再落笔**（见 `_unrec7b.txt` 生成方式）。' % exc[k])
    w('')

    if missing:
        w('## 6. 盘上缺的文件\n')
        for name, fn in missing:
            w('- %s → `bench_v1/%s`（**没有这个文件，不是"0 件"，是"没测过"**）' % (name, fn))
        w('')

    w('## 7. 读法与禁写\n')
    w('- 本表所有"率"的分母是**该臂实际生成的件数**，不是 64 题、也不是 192；跨臂比"率"只在两臂 n 相同时成立。\n')
    w('- 判定用的是 420s / R=10 / 40000，与生成侧 run_note 的预览超时（8B 前 5 件 300s、其后 60s）**无关**，'
      '所以生成侧那句"混口径"不污染本表。\n')
    w('- 不许从本表写"某端不行"：只许写"该端在这 192 件上，可编译/字段齐全/格级一致分别是多少"。\n')
    w('## 8. 正对照断言（本脚本自己也要被验一遍）\n')
    # 这四个数是 10-18 已发布在 LEGB_RESULT.md 里的 flash 臂读数；
    # 本脚本若把它们算成别的值，说明"合并/解析/分母"某一环被我改坏了，
    # 那么 7B 臂的 0/181 也就不可信。所以这条断言是给"0/181"作保的。
    KNOWN = {'compilable': (184, 192), 'complete': (165, 192),
             'cell': (144, 536), 'item': (34, 166)}
    fl = data.get('flash (DeepSeek)') or []
    bad = []
    if len(fl) != 192:
        w('- **无法验收**：flash 臂读到 %d 件，不是 192 件 ⇒ 断言跳过，本表不作保。\n' % len(fl))
    else:
        s = stats(fl)
        got = {'compilable': (s['compilable'], s['n']), 'complete': (s['complete'], s['n']),
               'cell': (s['cell_in'], s['cell_tot']), 'item': (s['item_all'], s['item_with_cells'])}
        bad = [k for k in KNOWN if KNOWN[k] != got[k]]
        for k in KNOWN:
            w('- %s：期望 %s，本脚本算出 %s ⇒ %s' % (
                k, KNOWN[k], got[k], '一致' if k not in bad else '**不一致**'))
        if bad:
            w('\n> 断言失败：%s ⇒ **本表不可用，先修脚本**' % ', '.join(bad))
        else:
            w('\n> 断言通过 ⇒ 同一套合并与判分代码在 flash 臂复现出已发布读数，'
              '所以 7B 臂的"格级一致 0/181"不是仪器错。')
    OUT.close()
    if bad and fl:
        sys.exit(1)

    print('OK')


if __name__ == '__main__':
    main()
