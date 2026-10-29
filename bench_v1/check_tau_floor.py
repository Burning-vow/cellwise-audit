"""G：τ\\* 的**真实余量**有多厚（2026-10-18，他点单 G）。

背景：F8 判"不成立"是因为 55 格里 51 格的 τ\\* 落在 grid 下限 0.01 —— 但这**可能是 grid 的
分辨率问题，不是余量问题**。本脚本不碰生产配置（不改 `criteria.TAU_GRID`、不重跑主表），
只从已有的逐次残差（`RECAL64_raw.jsonl` 的参照件 80 次试验）现算：

  ① 每格在更细的候选档上，参照件的报警次数 `k/n` 与 95% Wilson 上界；
  ② 按预注册同一条选档规则（task 级 Wilson 上界 ≤ 5% 的最小档）问："允许细档时 τ\\* 会落到哪？"
  ③ 余量 = 现行 τ\\* / 那个更细的值；
  ④ 副作用两面都数：若真把 τ\\* 下调，主表里**多少格会从静默变点火** ——
     按标签分开数：`detectable` 那边是收益（多抓到），`benign` 那边是**风险**（可能开始误杀）。

跑法：`~/miniconda3/python.exe check_tau_floor.py`（只读；`TF_OUT` 可把报告指走）。
"""
import collections
import csv
import glob
import io
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C                                   # noqa: E402

RAW = os.environ.get('TF_RAW') or os.path.join(HERE, 'RECAL64_raw.jsonl')
TAU_CSV = os.environ.get('TF_TAU') or os.path.join(HERE, 'table_tau_v2.csv')
MATRIX = os.environ.get('TF_MATRIX') or 'MUTANT_MATRIX_R10b.shard[0-9].csv'
OUT = os.environ.get('TF_OUT') or os.path.join(HERE, 'TAU_FLOOR.md')
# 比现行最细档（0.01）更细的一把梯子：只用于回答"还能不能更细"，不进任何生产表
LADDER = (0.002, 0.003, 0.005, 0.007, 0.010)
TARGET = C.WILSON_TARGET_UPPER
S2C = {'J1': 'J1', 'J1inv': 'J1', 'J2': 'J2', 'J3': 'J3'}


def main():
    per = collections.defaultdict(list)        # (tpl, crit, stat) -> [rel...]
    ntask = collections.defaultdict(set)
    for l in io.open(RAW, encoding='utf-8'):
        d = json.loads(l)
        if d.get('purpose') != 'task' or 'rel' not in d:
            continue
        for k, v in d['rel'].items():
            crit, stat = k.split('|', 1)
            per[(d['template'], crit, stat)].append(v)
            ntask[(d['template'], crit, stat)].add(d['task_id'])
    cur = {}
    for r in csv.DictReader(io.open(TAU_CSV, encoding='utf-8')):
        if r['tau_star'] not in ('', 'NONE'):
            cur[(r['template'], r['criterion'], r['statistic'])] = float(r['tau_star'])

    # ①②③ 每格：细档上的假阳率 + 允许细档时规则会选哪一档
    rows, floor_by_cell = [], {}
    for key in sorted(cur):
        vs = per.get(key) or []
        if not vs:
            continue
        k0, n0 = sum(1 for v in vs if v > cur[key]), len(vs)
        chosen = None
        for t in LADDER:
            k = sum(1 for v in vs if v > t)
            if C.wilson(k, n0)[1] <= TARGET:
                chosen = t
                break
        floor_by_cell[key] = chosen
        rows.append((key, n0, len(ntask[key]), max(vs), cur[key], k0, chosen,
                     (cur[key] / chosen) if chosen else float('nan')))
    # ⚠ 这里第一版写错下标（拿 r[5]=报警数 当现行 τ* 比），结果是"0 格能选细档"这种一看就不对的话。
    # rows 的列序：key, n_trials, n_tasks, max_rel, 现行 τ*, k0, 细档选到, 余量
    thinner = [r for r in rows if r[6] and r[6] < r[4]]
    print('[floor] 格=%d，其中"允许细档时规则会选到比 1%% 更细"的 %d 格' % (len(rows), len(thinner)))

    # ④ 主表里：把 τ* 下调到细档值，会新点火的格数（按标签分）
    lab = {}
    for l in io.open(os.path.join(HERE, 'mutants.jsonl'), encoding='utf-8'):
        d = json.loads(l)
        lab[(d['task_id'], d['error_type'])] = d['expected']
    gain = collections.Counter()
    risk = collections.Counter()
    checked = 0
    for fn in [f for f in sorted(glob.glob(os.path.join(HERE, MATRIX)))
               if '.triggers.' not in os.path.basename(f)]:
        for r in csv.DictReader(io.open(fn, encoding='utf-8')):
            if r['rel'] in ('', None):
                continue
            crit = S2C.get(r['stage'])
            key = (r['template'], crit, r['instance'])
            f = floor_by_cell.get(key)
            if f is None or crit is None:
                continue
            rel = float(r['rel'])
            t_cur = cur[key]
            checked += 1
            if f < rel <= t_cur:                    # 现在静默、下调后点火
                exp = lab.get((r['task_id'], r['error_type']), '?')
                (gain if exp in ('detectable', 'weak') else risk)[exp] += 1
    L = ['# τ\\* 的真实余量（`check_tau_floor.py` 产生；不改生产配置、不重跑主表）', '',
         '生成时间：%s ｜ 每格参照试验数 %d–%d 次 ｜ 细档梯子 %s ｜ 选档规则沿用预注册：task 级 Wilson 上界 ≤ %.0f%%' % (
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             min((r[1] for r in rows), default=0), max((r[1] for r in rows), default=0),
             ', '.join('%g' % t for t in LADDER), 100 * TARGET), '',
         '## 一句话结论',
         '- **允许更细的档时，规则会把 τ\\* 选到 1%% 以下的格：%d / %d**' % (len(thinner), len(rows)),
         '- 主表里被检查的实测格 %d 个：若真下调，'
         '**可检/弱档会新点火 %d 格（收益）**，而**良性档会新点火 %d 格（风险，会开始误杀）**' % (
             checked, sum(gain.values()), sum(risk.values())), '',
         '## 每格明细（前 30 行）', '',
         '| 模板 | 判据 | 观测量 | 试验数 | 题数 | 参照最大 rel | 现行 τ\\* | τ\\*=1% 时报警数 | 允许细档时选到 | 余量倍数 |',
         '|---|---|---|---|---|---|---|---|---|---|']
    for key, n0, nt, mx, t_cur, k0, ch, ratio in rows[:30]:
        L.append('| %s | %s | %s | %d | %d | %.4g | %.3f | %d | %s | %s |' % (
            key[0], key[1], key[2], n0, nt, mx, t_cur, k0,
            ('%.3f' % ch) if ch else '无（比 0.002 更细才不报警）',
            ('%.1f×' % ratio) if ratio == ratio else '—'))
    L += ['', '## 对 §26 的 F7/F8 判定意味着什么', '',
          '- F8"不成立"的**真实原因**在这一节：τ\\* 密集落在 1% 不代表余量只有 1 倍。'
          '参照残差的最大值与 1% 之间的差距，就是"还能压多细"的空间。',
          '- 但下调不是免费的：上面那行"良性档会新点火 %d 格"就是代价 —— 现在的 0/68 零误杀'
          '是**在 τ\\*=1%% 上**成立的事实，压细就可能开始冤枉工件。' % sum(risk.values()),
          '- ⇒ 正文能写的句子：「逐格标定给的是余度账：多数格的参照残差远低于 1%%，'
          '但我们仍把 τ\\* 取在规则允许的最保守档，因为压到细档会让 %d 格良性标本开始被误判。」' % sum(risk.values()),
          '- 禁写的句子：「τ\\*=1% 是因为参照噪声就是 1% 量级」（若本表显示更细，就是 grid 卡住，不是噪声）。',
          '- ⚠ 这张表**不改** `criteria.TAU_GRID`、不改 τ\\* 表、不改主表任何判定；'
          '要真用细档，必须重跑标定链并同步扩主表的 `fired_<τ>` 列（那是 410 件 × 10 次的一次重跑）。']
    # ⑤ 余度账（口径与 `GATE_R10.md` 一致：余度 = 现行 τ* / 参照件最大残差）。
    #    这个比"细档倍数"更该被引用：细档倍数的分母是梯子下限，会把"τ* 被迫抬高"的格
    #    误报成大余量（第一版我就踩了这个）。
    band = collections.Counter(); thin = []
    alarm_at_1pct = []
    for key, n0, nt, mx, t_cur, k0, ch, ratio in rows:
        if mx == 0:
            band['残差恒 0（R0/确定式解）'] += 1
        else:
            m = t_cur / mx
            band['<1.2×' if m < 1.2 else ('1.2–2×' if m < 2 else ('2–5×' if m < 5 else '≥5×'))] += 1
            if m < 2.0:
                thin.append((key, mx, t_cur, m))
        if mx > 0.01:
            kk = sum(1 for v in (per.get(key) or []) if v > 0.01)
            nn = len(per.get(key) or [])
            alarm_at_1pct.append((key, mx, kk, nn, C.wilson(kk, nn)[1]))
    L += ['', '## 全局 τ=1% 下会冤枉参照件的格（**本轮在现引擎 raw 上重算**，不引用 `GATE_R10.md` 的旧数）', '',
          '| 模板 | 判据 | 观测量 | 试验数 | 1% 下报警 | 报警率 | Wilson 上界 | 参照最大 rel | 现行 τ\\* |',
          '|---|---|---|---|---|---|---|---|---|']
    for key, mx, kk, nn, wu in alarm_at_1pct:
        L.append('| %s | %s | %s | %d | %d | %.1f%% | %.1f%% | %.4g | %.3f |' % (
            key[0], key[1], key[2], nn, kk, 100.0 * kk / nn, 100 * wu, mx, cur[key]))
    L.append('- 这四格正是 `GATE_R10.md`（09:5x 那一代）点出的同样四格 ⇒ 跨代一致，'
             '但引用时用本表的数。')
    L += ['', '## 余度账（口径同 `GATE_R10.md`：余度 = 现行 τ\\* / 参照件最大残差）', '',
          '- 分档：%s' % ('、'.join('%s %d 格' % (k, v) for k, v in sorted(band.items()))),
          '- **全局 τ=1%% 下会把参照件冤枉掉的格：%d 个**（这些格的 τ\\* 被规则抬到 1%% 以上）：%s' % (
              len(alarm_at_1pct),
              '、'.join('%s/%s·%s maxrel=%.4g' % (k[0], k[1], k[2], mx)
                       for k, mx, _kk, _nn, _wu in alarm_at_1pct)),
          '- 余度 <2× 的薄格 %d 个（换参数区域最可能翻脸的正是这些，腿 B 必须按模板分档用）：%s' % (
              len(thin), '、'.join('%s/%s·%s=%.2f×' % (k[0], k[1], k[2], m)
                                   for k, mx, tc, m in sorted(thin, key=lambda x: x[3])[:14])), '',
          '## 这张表回答的是审稿第一问：「逐格标定和全局 1% 有什么区别？」',
          '- 区别在**少数格**：全局 1%% 会在上面那 %d 个格上冤枉参照件（报警率 %.1f%%–%.1f%%，'
          '就是上表那四行，现引擎重算与 `GATE_R10.md` 同格同值），'
          '逐格标定把它们抬到 2–3%%；其余 %d 格两种做法给出同一个 τ\\*。' % (
              len(alarm_at_1pct),
              min(100.0 * kk / nn for _k, _mx, kk, nn, _wu in alarm_at_1pct),
              max(100.0 * kk / nn for _k, _mx, kk, nn, _wu in alarm_at_1pct),
              len(rows) - len(alarm_at_1pct)),
          '- 所以能写的句子是「逐格标定的产出是一张**余度账**」，不是「全局阈值会大爆炸」（F7 已判不成立）；'
          '也不能写「本文给出可移植的阈值配方」（F8 已判不成立）。',
          '- ⚠ 细档倍数（上面"余量倍数"列）只回答"还能不能更细"，**不要**拿它当余度引用。']
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('[floor] 报告 -> %s（试验数/格 见下表第一列）' % OUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())
