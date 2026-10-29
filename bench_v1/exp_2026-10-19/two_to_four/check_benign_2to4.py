"""良性件自证闸（#17 的第二半）：凡 expected=benign 的对照件，必须先证明
   它报出来的数在**该格自己的 τ\\*** 下与闭式真值一致，否则不许标 benign。

为什么需要它：E28、E35 两族原来都标 benign，实测一个把 W 改 60 倍、一个把 cost 改 365 倍。
   若不查，我会把 27% 的"判据假阳率"写进论文——而那 100% 是我自己标错。
   良性对照是量假阳率的分母，分母本身是坏的，整张表就是空的。

用法：python check_benign.py --shard=1/2
输出：BENIGN_PROOF.csv（逐件 flush）+ BENIGN_PROOF.md（按错型汇总）
"""
import csv
import json
import os
import sys
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)
import criteria as C  # noqa: E402
from inv_obs import j1_inv  # noqa: E402

ART = os.path.join(BENCH, 'artifacts')
OUT = os.path.join(HERE, 'BENIGN_PROOF_2to4.csv')
MUT = os.path.join(HERE, 'mutants_2to4.jsonl')
SEEDS = 10          # 必须等于 τ* 的标定预算（table_tau_v2 的 tau_basis_seeds=10）；原来这里是 20，
# 而这张表是良性类标签的权威产物 —— 权威自己跨预算比阈值，等于权威不可用
HOR = 40000.0
# E35 已由实测改判 detectable（cost 差 365 倍），不再当良性对照
RELABELED = {}   # 改判已写回标签源头（mutants.jsonl + simcore.CATALOG）；成员集合一致性由 selfcheck_all 第 6 项断言，不在这里另立一份
TAU = {}
for r in csv.DictReader(open(os.path.join(BENCH, 'table_tau_v2.csv'), encoding='utf-8')):
    if r['tau_star'] not in ('', 'NONE'):
        TAU[(r['criterion'], r['statistic'], r['template'])] = float(r['tau_star'])
BASIS = {int(r['tau_basis_seeds']) for r in
         csv.DictReader(open(os.path.join(BENCH, 'table_tau_v2.csv'), encoding='utf-8'))
         if r['tau_star'] not in ('', 'NONE')}     # 良性自证用的种子数必须等于 τ* 的标定预算


assert BASIS == {SEEDS}, '良性自证闸的 SEEDS=%d 与 τ* 的标定预算 %s 不一致 ⇒ 停下' % (SEEDS, sorted(BASIS))


def judge(obs, task):
    """返回 (是否合格, 超阈的格列表)。合格 = 所有可判格 rel <= 该格 τ*。"""
    bad = []
    judged = 0
    items = list(C.j1_analytic(obs, task, tau=None)['per_obs'].items())
    items += list(j1_inv(obs, task).items())
    for o, d in items:
        if d.get('rel') is None:
            continue
        # ⚠ 原来这里写 `TAU.get(..., 0.01)`——给没标定的格子发一个**默认阈值**。
        #   这张表是"良性类的标签权威"，发默认值等于我自己造一个假标准（审计 P-15；
        #   `summarize_matrix_v2.py` 开头就写了"绝不给默认值"，同一条规矩不能两头不一样）。
        if ('J1', o, task['template']) not in TAU:
            raise SystemExit('J1/%s 在 %s 上没有标定 τ* ⇒ 良性自证不许用默认阈值顶替，停下'
                             % (o, task['template']))
        t = TAU[('J1', o, task['template'])]
        judged += 1
        if d['rel'] > t:
            bad.append('J1/%s rel=%.5f>τ*=%.3f' % (o, d['rel'], t))
    for cn, fn in (('J2', C.j2_conservation), ('J3', C.j3_pairing)):
        for kk, d in (fn(obs, task, tau=None).get('per_stat') or {}).items():
            if d.get('rel') is None:
                continue
            if (cn, kk, task['template']) not in TAU:
                raise SystemExit('%s/%s 在 %s 上没有标定 τ* ⇒ 停下，不发默认阈值'
                                 % (cn, kk, task['template']))
            t = TAU[(cn, kk, task['template'])]
            judged += 1
            if d['rel'] > t:
                bad.append('%s/%s rel=%.5f>τ*=%.3f' % (cn, kk, d['rel'], t))
    return (judged > 0 and not bad), bad, judged


def main():
    shard, nshard = 1, 1
    for a in sys.argv[1:]:
        if a.startswith('--shard='):
            shard, nshard = [int(x) for x in a.split('=')[1].split('/')]
    done = set()
    if os.path.exists(OUT):
        for r in csv.DictReader(open(OUT, encoding='utf-8')):
            if 'seeds' not in r:
                raise SystemExit('BENIGN_PROOF.csv 是旧格式（没有 seeds 列）⇒ 分不清是哪档预算产出的，'
                                 '先归档再重跑，不许在陈旧口径上续跑')
            done.add((r['task_id'], r['error_type'], r['seeds'], r['horizon']))
    ms = [json.loads(l) for l in open(MUT, encoding='utf-8')]
    exp = {(m['task_id'], m['error_type']): RELABELED.get(m['error_type'], m['expected']) for m in ms}
    todo = [m for m in ms
            if exp.get((m['task_id'], m['error_type'])) == 'benign'
            and (m['task_id'], m['error_type'], str(SEEDS), str(HOR)) not in done]
    todo = todo[(shard - 1)::nshard]
    new = not os.path.exists(OUT)
    fh = open(OUT, 'a', newline='', encoding='utf-8')
    def wrow(vals):
        _w.writerow(list(vals) + [SEEDS, HOR])   # 每行自带口径，续跑键与旧格式检测都靠它

    _w = csv.writer(fh)
    if new:
        _w.writerow(['task_id', 'template', 'error_type', 'n_judged', 'verdict', 'violations',
                     'seeds', 'horizon'])
        fh.flush()
    by_id = {t['task_id']: t for t in C.load_tasks()}
    t0 = time.time()
    print('[benign %d/%d] todo=%d' % (shard, nshard, len(todo)), flush=True)
    for i, m in enumerate(todo, 1):
        tid, et = m['task_id'], m['error_type']
        path = os.path.join(ART, '%s__%s.py' % (tid, et))
        if not os.path.exists(path):
            wrow([tid, m['template'], et, 0, 'MISSING', ''])
            fh.flush()
            continue
        obs, dt, note = C.run_artifact(path, SEEDS, HOR, 'none', 1)
        if obs is None:
            wrow([tid, m['template'], et, 0, 'CRASH', str(note)[-140:]])
            fh.flush()
            continue
        ok, bad, judged = judge(obs, by_id[tid])
        wrow([tid, m['template'], et, judged, 'PROVES_BENIGN' if ok else 'NOT_BENIGN',
                    '; '.join(bad)[:200]])
        fh.flush()
        if not ok:
            print('[benign] ! %s %s 不合格: %s' % (tid, et, '; '.join(bad)[:120]), flush=True)
        if i % 5 == 0 or i == 1:
            print('[benign %d/%d] %d/%d %.0fs' % (shard, nshard, i, len(todo), time.time() - t0),
                  flush=True)
    fh.close()


if __name__ == '__main__':
    main()
