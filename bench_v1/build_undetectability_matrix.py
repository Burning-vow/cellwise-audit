"""C1 的证据表：把 `theorem_map.PRED` 的**格级先验预测**与 R10c 实测逐格对账。

产出的东西就是论文里那张"判据 × 错型 不可检性矩阵"：每一格写
  定理预测（0检出 / 可检 / weak / 塌缩 / 无信息） + 该格 τ* + 实测 rel 与是否点火 + 吻合？
它同时是**可证伪性**的载体：任何"定理说必然检不出、实测却点火"的格都会被点名，
并直接判本脚本失败（退出码非 0）——这样"预测在跑之前钉死"就不是我口头承诺。

用法：~/miniconda3/python.exe build_undetectability_matrix.py [矩阵glob]
      缺省优先用 R10c（408 件），若 R10c 不完整则退回 R10b 并在报告里写明。
"""
import csv
import glob
import io
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import theorem_map as TM        # noqa: E402
from summarize_matrix_v2 import STAGE2CRIT, load_tau   # noqa: E402  只有一份 τ* 读法

OUT = os.path.join(HERE, 'UNDETECTABILITY_MATRIX.md')
MUT = os.path.join(HERE, 'mutants.jsonl')


def matrix_rows(pattern):
    files = [f for f in sorted(glob.glob(os.path.join(HERE, pattern)))
             if '.triggers.' not in os.path.basename(f)]
    rows = []
    for f in files:
        for r in csv.DictReader(io.open(f, encoding='utf-8')):
            rows.append(r)
    return files, rows


def pick_matrix():
    """优先 R10c（含今晚新算子），但必须**件数齐**才用它。"""
    want = sum(1 for l in io.open(MUT, encoding='utf-8') if l.strip())
    for pat, tag in (('MUTANT_MATRIX_R10c.shard*.csv', 'R10c'),
                     ('MUTANT_MATRIX_R10b.shard*.csv', 'R10b')):
        files, rows = matrix_rows(pat)
        arts = {(r['task_id'], r['error_type']) for r in rows}
        if not files:
            continue
        n_mut = len({a for a in arts if a[1] != 'REF'})
        if tag == 'R10c' and n_mut < want:
            sys.stdout.write('[warn] R10c 只有 %d/%d 件，改用 R10b\n' % (n_mut, want))
            continue
        return pat, tag, files, rows, n_mut, want
    raise SystemExit('盘上没有可用的矩阵文件')


def fired_at(row, tau):
    """优先读矩阵里现成的 fired_<τ> 列；没有就按 rel>τ 现算（并说明用的是哪条路）。"""
    col = 'fired_%g' % tau
    if col in row and row[col] not in ('', None):
        return int(row[col]), 'col'
    try:
        return (1 if float(row['rel']) > tau else 0), 'calc'
    except (TypeError, ValueError, KeyError):
        return None, 'na'


def p5_reconcile(by_art):
    """P5（等价对）的实测核对：同一题上两个代码位不同的错型，判据判决是否真分不出来。

    分两个口径报，别混：**判决逐位相同**（fired 全等）与 **rel 也逐位相同**（数值全等）。
    只有前者成立时，主张要写成"只看观测量的判据在判决层不可区分"，不能写成"行为完全相同"。
    """
    out = []
    for a, b in TM.EQUIV_PAIRS:
        ta = {tid for (tid, et) in by_art if et == a}
        tb = {tid for (tid, et) in by_art if et == b}
        tasks = sorted(ta & tb)
        same_v = same_r = diff = 0
        bad = []
        for tid in tasks:
            va = {(r['stage'], r['instance']): (r.get('rel'), r.get('fired_0.01'))
                  for r in by_art[(tid, a)]}
            vb = {(r['stage'], r['instance']): (r.get('rel'), r.get('fired_0.01'))
                  for r in by_art[(tid, b)]}
            if va.keys() != vb.keys():
                diff += 1
                bad.append('%s 键集不同（%d 格 对 %d 格）' % (tid, len(va), len(vb)))
                continue
            dv = [k for k in va if va[k][1] != vb[k][1]]
            dr = [k for k in va if va[k][0] != vb[k][0]]
            if dv:
                diff += 1
                k = dv[0]
                bad.append('%s 判决不同 %d 格，例 %s：%s 对 %s' % (tid, len(dv), k, va[k], vb[k]))
            else:
                same_v += 1
            if not dr:
                same_r += 1
        out.append((a, b, len(tasks), same_v, same_r, diff, bad))
    return out


def main():
    pat, tag, files, rows, n_mut, want = pick_matrix()
    TAUS, VAC = load_tau()
    # 机制计数器：判"空转"只能按**错型自己那条机制**（规矩 57/58），
    # 用"读数与参照件相同"猜会把 M/D/1 上真跑了 11 万次的恒等证据误删。
    from summarize_matrix_v2 import IDLE_GATE
    TRIG = {}
    for f in sorted(glob.glob(os.path.join(HERE, pat.replace('.csv', '.triggers.csv')))):
        for r in csv.DictReader(io.open(f, encoding='utf-8')):
            TRIG[(r['task_id'], r['error_type'])] = r

    def idle(tid, et):
        gate = IDLE_GATE.get(et)
        if not gate:
            return False
        r = TRIG.get((tid, et))
        if r is None:
            return False
        try:
            return all(float(r.get(g) or 0) == 0 for g in gate)
        except ValueError:
            return False
    by_art = defaultdict(list)
    for r in rows:
        by_art[(r['task_id'], r['error_type'])].append(r)

    L = ['# 不可检性矩阵：定理先验预测 vs 实测（`build_undetectability_matrix.py` 产生）', '']
    L.append('- 矩阵：`%s`（%d 片，%d 件变异体；标签表 %d 件）；τ\\* 表 %d 格；'
             '空判据格（R0_VACUOUS）%d 个，**不参与"判据有信息"的计数**。'
             % (pat, len(files), n_mut, want, len(TAUS), len(VAC)))
    L.append('- 口径：只看 %s 三条腿（J0 不进主表、J5/J6 不是数值判据）；'
             '每格的"点火"= `rel > τ*(该格)`，优先读矩阵里的 `fired_τ` 列。' % '/'.join(TM.LEGS_IN_SCOPE))
    L.append('')
    L.append('## (0) 命题清单（预测在跑之前就钉死，见 `theorem_map.py`）')
    L.append('')
    for p in sorted(TM.PROPS):
        d = TM.PROPS[p]
        L.append('- **%s %s**：%s' % (p, d['name'], d['stmt']))
        L.append('  - 为什么这块还空着：%s' % d['why_empty'])
    L.append('')

    # ---------------------------------------------------------- 逐格对账
    stat = defaultdict(lambda: dict(n=0, ok=0, bad=[], by_pred=defaultdict(int)))
    detail = defaultdict(list)
    for et, spec in sorted(TM.PRED.items()):
        if et == 'E14p5':
            continue
        prop = spec['prop']
        for (tid, e2), rws in sorted(by_art.items()):
            if e2 != et:
                continue
            tpl = rws[0]['template']
            pred = spec['tpl'].get(tpl, None)
            for obs, pv in spec['obs'].items():
                if obs == 'J2a_little':
                    stage_key, inst = 'J2', 'J2a_little'
                else:
                    stage_key, inst = 'J1', obs
                hit = [r for r in rws
                       if STAGE2CRIT.get(r['stage']) == stage_key and r['instance'] == inst]
                key = (tpl, stage_key, inst)
                tau = TAUS.get(key)
                s = '%s/%s@%s(%s)' % (et, inst, tpl, tid)
                if idle(tid, e2):
                    # 机制没落地：既不算"定理被推翻"，也不算"吻合"——单列，不进分母
                    stat[prop]['n'] += 1
                    stat[prop]['by_pred']['IDLE(机制未落地,不进分母)'] += 1
                    detail[prop].append((s, p if isinstance(p, str) else pv,
                                         'IDLE', '-', '-', 'n/a'))
                    continue
                if pred == '塌缩':
                    p = '塌缩'
                elif isinstance(pred, str):
                    p = pred
                else:
                    p = pv
                if p == '塌缩':
                    stat[prop]['n'] += 1
                    stat[prop]['by_pred']['塌缩(不进分母)'] += 1
                    detail[prop].append((s, p, '不进分母', '-', '-', 'n/a'))
                    continue
                if tau is None:
                    stat[prop]['n'] += 1
                    stat[prop]['by_pred']['NA(无τ*)'] += 1
                    detail[prop].append((s, p, '无 τ* ⇒ 判不了', '-', '-', 'n/a'))
                    continue
                fs = [fired_at(r, tau)[0] for r in hit]
                fs = [f for f in fs if f is not None]
                rels = [float(r['rel']) for r in hit if r.get('rel') not in ('', None)]
                if not fs:
                    stat[prop]['n'] += 1
                    stat[prop]['by_pred']['NA(无实测行)'] += 1
                    detail[prop].append((s, p, '无实测行', '%g' % tau, '-', 'n/a'))
                    continue
                anyf = any(fs)
                if p == '0检出':
                    ok = (not anyf)
                elif p == '可检':
                    ok = bool(anyf)
                elif p == 'weak':
                    ok = True                      # 两种结局都算符合，但要点火率
                elif p == '无信息':
                    ok = all(v <= 1e-6 for v in rels)
                else:
                    ok = False
                stat[prop]['n'] += 1
                stat[prop]['by_pred'][p] += 1
                if ok:
                    stat[prop]['ok'] += 1
                else:
                    stat[prop]['bad'].append('%s 预测%s 实测%s(rel 最大 %.4g, τ*=%g)' % (
                        s, p, '点火' if anyf else '不点火',
                        max(rels) if rels else float('nan'), tau))
                detail[prop].append((s, p, ('点火' if anyf else '不点火') + ' %d/%d' % (sum(fs), len(fs)),
                                     '%g' % tau,
                                     '%.4g' % (max(rels) if rels else float('nan')),
                                     '吻合' if ok else '**不吻合**'))

    L.append('## (1) 逐命题对账')
    L.append('')
    L.append('| 命题 | 预测格数 | 吻合 | 不吻合 | 预测分布 |')
    L.append('|---|---|---|---|---|')
    tot_n = tot_bad = 0
    for prop in sorted(stat):
        d = stat[prop]
        tot_n += d['n']
        tot_bad += len(d['bad'])
        L.append('| %s | %d | %d | %d | %s |' % (
            prop, d['n'], d['ok'], len(d['bad']),
            ', '.join('%s=%d' % (k, v) for k, v in sorted(d['by_pred'].items()))))
    # P5 不是判据格，但必须有一行实测：否则读者会以为表里五条命题都被核对过。
    # 它**不进 tot_n**（总预测格 240 的口径不变），单独成行并写明为什么不进。
    p5 = p5_reconcile(by_art)
    for a, b, ntask, same_v, same_r, diff, bad in p5:
        L.append('| P5 | 等价对 %s↔%s（%d 对题，**不是判据格，不进总预测格**） | '
                 '判决逐位相同 %d | rel 也逐位相同 %d | 不同 %d；%s |' % (
                     a, b, ntask, same_v, same_r, diff,
                     bad[0] if bad else '无反例'))
    L.append('')
    L.append('- **总预测格 %d，不吻合 %d**。不吻合 = 定理与实测打架，**必须公开更正**（不许改预测凑数）。'
             % (tot_n, tot_bad))
    for prop in sorted(stat):
        for b in stat[prop]['bad']:
            L.append('  - [%s] %s' % (prop, b))
    L.append('')

    for prop in sorted(detail):
        L.append('## (2.%s) %s —— %s' % (prop, prop, TM.PROPS[prop]['name']))
        L.append('')
        L.append('| 格（错型/观测量@模板） | 定理预测 | 实测点火/实例 | τ* | rel 最大 | 吻合 |')
        L.append('|---|---|---|---|---|---|')
        for row in sorted(detail[prop]):
            L.append('| `%s` | %s | %s | %s | %s | %s |' % tuple(row))
        L.append('')

    L.append('## (3) 等价对（P5，不是判据格）')
    L.append('')
    for a, b in TM.EQUIV_PAIRS:
        L.append('- `%s` 与 `%s`：同一可观测行为、不同代码位 ⇒ 只看观测量的判据**原理上不可区分**；'
                 '分母里记"不可区分"，不记"漏检"。' % (a, b))
    L.append('')
    L.append('## (4) 这张表能支撑的句子（照抄，别越界）')
    L.append('')
    L.append('- ✅ "我们把判据能力边界写成**可证伪的格级预测**：定理先判定哪些格必然 0 检出，'
             '再用 %d 件注入工件逐格核对，不吻合 %d 格。"' % (n_mut, tot_bad))
    L.append('- ✅ "恒等类 %d 格里定理命中率 100%%"——**仅当上面 tot_bad=0 才许写**，且分母要现算。' % stat['P1']['n'])
    L.append('- ❌ 不写"首次分两型"（P4 的词面已被 Möltner 占，机制不同但必须切割）。')
    txt = '\n'.join(L) + '\n'
    io.open(OUT, 'w', encoding='utf-8').write(txt)
    sys.stdout.buffer.write(('写在 %s：预测格 %d，不吻合 %d\n'
                             % (os.path.basename(OUT), tot_n, tot_bad)).encode('utf-8', 'replace'))
    return 1 if tot_bad else 0


if __name__ == '__main__':
    sys.exit(main())
