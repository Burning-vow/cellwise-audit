"""F6 的实测链：把"样本预算 R"当**被扫的自变量**，用独立块重采样测检出率。

F6（预注册 §4 / §26 里唯一"本地能测但没测"那行）原文：
    |δ|∈[3%,6%] 的格 ⇒ R=20 检出率<50%，R=100 检出率>80%。若是 P2 右列那种"被定理保护"的格，
    R 再大也不该变。

为什么不能用现成表白嫖（本轮先试过、作废）：主表"带内格"的定义本身就是 `rel>τ*`，
所以"它们在 R=10 上 100% 点火"是**恒真**，抓不到预算效应（规则：交叉核对两边同源=恒真）。
真测必须有**同一格、同一判据、多个独立预算估计** ⇒ 只能重跑。

三条硬约束（不是偏好）：
 1. **判分端一字不改**：照 `run_mutant_matrix.py` 的四个出口（J1 / J1inv→J1 / J2 / J3）调用，
    只把 `seeds` 换成臂预算 R。换尺子就不是 F6。
 2. **块之间独立、且与"选带用过的那 10 个种子"不重叠**：411 件工件里 `per_seed_*` 出现 **0 次**
    （盘上 grep 过），工件只报聚合均值 ⇒ 一个块 = 一次子进程调用，用
    `seed_start = F6_SEED0 + (arm_offset + b) * R` 取互不相交的 seed 段；默认 SEED0=1000
    ⇒ 与主表的 seed 1..10 完全隔开，"因为选中它才点火"的回归均值不会伪装成检出率。
 3. **不做跨臂池化算术**：曾经想用 50 个 R=10 块拼出 R=100，但那要对 |·| 取平均后再取绝对值，
    而 `J2b/J2c/J3a` 的 per_stat 里没有存两边原始均值 ⇒ 拼不出可审计的等价物。
    现在每条臂自己跑自己的 R，`rel` 全部出自同一个 `criteria`，代价是多花机时，换来的是
    产物每一行都能被独立复算。

分层（两条，先钉规则再跑）：
  band  = 题面的带 0.03 ≤ rel(R=10) ≤ 0.06
  near  = 靠近自己 τ* 的带 0.5·τ* ≤ rel ≤ 1.5·τ* 且 rel ≥ 0.005
          （旧版写成 `rel/τ*<1.5`，把 rel≈0 的格也当"近阈值"——那是"没效应"，不是靠近阈值。）
为什么两条一起跑：题面带里的格几乎全是 δ/τ*≈3–6×，若它们对任何 R 都接近 100% 点火，
F6 的死因就是"本文语料里没有靠近阈值的带内格"；而 `near` 层给出真正会随 R 变的那一段。
两档合起来才是一条可写的曲线，而不是只有"预测不成立"。

用法：
  ~/miniconda3/python.exe run_f6_budget.py                      # 默认 10 件 × 三臂
  F6_KEYS=1 F6_ARMS=20:1 ~/miniconda3/python.exe run_f6_budget.py   # 单块实炮（先验管道）
  F6_PREVIEW=1 ~/miniconda3/python.exe run_f6_budget.py         # 只列选中的件与格，不跑
"""
import csv
import io
import json
import os
import sys
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C  # noqa: E402
from inv_obs import j1_inv  # noqa: E402
from summarize_matrix_v2 import load_tau, STAGE2CRIT  # noqa: E402

SHARDS = [os.path.join(HERE, 'MUTANT_MATRIX_R10b.shard%d.csv' % i) for i in (1, 2, 3, 4)]
ART = os.path.join(HERE, 'artifacts')
MUT = os.path.join(HERE, 'mutants.jsonl')
OUT = os.environ.get('F6_OUT') or os.path.join(HERE, 'F6_BLOCKS.csv')
ARMS = [(int(a.split(':')[0]), int(a.split(':')[1]))
        for a in (os.environ.get('F6_ARMS') or '10:25,20:25,100:10').split(',')]
SEED0 = int(os.environ.get('F6_SEED0', 1000))      # 与主表 seed 1..10 隔开
ARM_STRIDE = int(os.environ.get('F6_ARM_STRIDE', 100000))
# ⚠ 逐臂分种子段（10-18 自己踩的坑）：旧写法是"每条臂都从 SEED0 重新数偏移"，
# 于是 R=100 的第 0、1 块（种子 1000–1199）恰好**包含**R=20 那 10 块的全部种子 ⇒ 两臂不独立，
# "两条臂独立采样"这句写不成（合并检出率本身无偏，所以这是个可检出的方法学缺陷而非数值错）。
# 现在臂 i 固定占 [SEED0+i*ARM_STRIDE, +R*nb)，并开跑前断言互不相交。


def used_spans():
    """盘上已经占用的 seed 段，按 R 分组。续跑同 R 合法（那本来就是同一批 seed），
    但**不同 R 之间必须互不相交**，否则两条预算臂共享样本 ⇒ "两臂独立"这句写不成。
    """
    spans = {}
    if os.path.exists(OUT):
        with io.open(OUT, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                try:
                    R = int(r['R'])
                    s0 = int(r['seed_start'])
                except (TypeError, ValueError):
                    continue
                lo, hi = spans.setdefault(R, [s0, s0 + R - 1])
                spans[R] = (min(lo, s0), max(hi, s0 + R - 1))
    return spans


def check_arm_ranges():
    rng = []
    for ai, (R, nb) in enumerate(ARMS):
        base = SEED0 + ai * ARM_STRIDE          # 逐臂分段，见 ARM_STRIDE 的注释
        rng.append((base, base + R * nb - 1, R))
    for i in range(len(rng) - 1):               # 本次调用内部
        if rng[i][1] >= rng[i + 1][0] and rng[i][2] != rng[i + 1][2]:
            raise SystemExit('臂种子段相交 ⇒ %s 与 %s 重叠；两臂不许共享 seed'
                             % (rng[i][:2], rng[i + 1][:2]))
    for (lo, hi, R) in rng:                     # 与盘上已有的**别的 R**
        for R2, (l2, h2) in sorted(used_spans().items()):
            if R2 == R:
                continue
            if lo <= h2 and l2 <= hi:
                raise SystemExit('R=%d 计划用 [%d,%d]，与盘上 R=%d 已用的 [%d,%d] 重叠 '
                                 '⇒ 两条预算臂会共享 seed。改 F6_SEED0 到未占用区段再跑。'
                                 % (R, lo, hi, R2, l2, h2))
    return rng
HOR = float(os.environ.get('F6_HOR', 40000.0))
N_KEYS = int(os.environ.get('F6_KEYS', 10))
BAND = (0.03, 0.06)
NEAR_MIN_REL = 0.005                                # rel 低于此不算"近阈值"，算"没效应"
HEAD = ['key', 'task_id', 'template', 'error_type', 'family', 'criterion', 'statistic',
        'R', 'block', 'seed_start', 'horizon', 'rel', 'tau_star', 'fired', 'stratum',
        'wall_s', 'note']


def emit(s=''):
    """字节安全落 stdout：控制台是 cp936 时打 '⇒' 会先崩在编码上，
    症状是 rc=1、'链没起来'，而其实什么都没跑（本机老坑，见规矩：子进程要给 PYTHONIOENCODING）。
    ⚠ 必须 flush：`sys.stdout.buffer` 默认全缓冲，14:35 起那 50 分钟的逐件进度全卡在缓冲区里，
    日志只有一行 `phase A start` ⇒ 看起来像"链卡死"。数据 CSV 一直逐块 flush，所以没丢读数为。"""
    sys.stdout.buffer.write((str(s) + chr(10)).encode('utf-8', 'replace'))
    sys.stdout.buffer.flush()


def strata(rel, tau):
    s = []
    if BAND[0] <= rel <= BAND[1]:
        s.append('band')
    if rel >= NEAR_MIN_REL and 0.5 * tau <= rel <= 1.5 * tau:
        s.append('near')
    return '+'.join(sorted(s))


def candidate_cells():
    """从现行 R=10 主矩阵取候选格（题面带 ∪ 近阈值带）。只读，不改任何判定。"""
    TAU, VAC = load_tau()
    cells = []
    n_rows = 0
    for p in SHARDS:
        with io.open(p, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                n_rows += 1
                crit = STAGE2CRIT.get(r['stage'])
                if crit is None or r['rel'] in ('', None):
                    continue
                try:
                    rel = float(r['rel'])
                except ValueError:
                    continue
                k = (r['template'], crit, r['instance'])
                tau = TAU.get(k)
                if tau is None or k in VAC:
                    continue                       # 未标定 / 空判据 ⇒ 都不进 F6 分母
                st = strata(rel, tau)
                if st:
                    cells.append(dict(key=r['key'], task_id=r['task_id'],
                                      template=r['template'], et=r['error_type'],
                                      family=r['family'], crit=crit, inst=r['instance'],
                                      rel=rel, tau=tau, strat=st))
    return cells, TAU, n_rows


def pick_keys(cells, n):
    """分层配额：按 (template, stratum) 每层取"该层格数最多"的一件，跨层去重；
    剩下的名额再按总带内格数补。规则先钉死再跑，不许看完结果再挑（不事后改判据）。"""
    by_key = defaultdict(list)
    for c in cells:
        by_key[c['key']].append(c)
    layer = defaultdict(list)
    for kk, cs in by_key.items():
        tpl = cs[0]['template']
        for st in ('band', 'near'):
            m = [c for c in cs if st in c['strat'].split('+')]
            if m:
                layer[(tpl, st)].append((len(m), kk))
    chosen, seen = [], set()
    for (tpl, st) in sorted(layer):
        lst = sorted(layer[(tpl, st)], key=lambda x: (-x[0], x[1]))
        for _, kk in lst:
            if kk not in seen:
                chosen.append(kk)
                seen.add(kk)
                break
    # 名额语义（10-18 被自己咬过一次）：`F6_KEYS` 截的是**层顺序**，不是随机件。
    # 生产跑给 F6_KEYS=18 = 全部 (模板×层)，截断等于"按模板字母序丢层"，缩样时要说清丢了哪几层。
    for kk in sorted(by_key, key=lambda k: (-len(by_key[k]), k)):
        if len(chosen) >= n:
            break
        if kk not in seen:
            chosen.append(kk)
            seen.add(kk)
    return chosen[:n], by_key


def judge(obs, task):
    """与 run_mutant_matrix.py 同源的四个出口，逐格给 (criterion, statistic, rel, status)。"""
    got = []
    j1 = C.j1_analytic(obs, task, tau=None)
    for o, d in j1['per_obs'].items():
        got.append(('J1', o, d.get('rel'), d.get('status', '')))
    for o, d in j1_inv(obs, task).items():
        got.append(('J1', o, d.get('rel'), d.get('status', '')))
    for cname, fn in (('J2', C.j2_conservation), ('J3', C.j3_pairing)):
        res = fn(obs, task, tau=None)
        for k2, d in (res.get('per_stat') or {}).items():
            got.append((cname, k2, d.get('rel'), d.get('status', '')))
    return got


def main():
    ms = [json.loads(l) for l in io.open(MUT, encoding='utf-8') if l.strip()]
    meta = {m['task_id'] + '__' + m['error_type']: m for m in ms}
    by_id = {t['task_id']: t for t in C.load_tasks()}
    cells, TAU, n_rows = candidate_cells()
    chosen, by_key = pick_keys(cells, N_KEYS)
    done = set()
    if os.path.exists(OUT):
        with io.open(OUT, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                done.add((r['key'], r['R'], r['block']))
    n_seeds = sum(R * nb for R, nb in ARMS)
    emit('[f6] 分片行=%d 候选格=%d/涉及件=%d | 选中件=%d 覆盖候选格=%d | 已完成块=%d'
          % (n_rows, len(cells), len(by_key), len(chosen),
             sum(len(by_key[k]) for k in chosen), len(done)))
    emit('[f6] 臂=%s ⇒ 每件 %d 个种子、%d 次调用（耗时由本链实测，不外推）'
          % (','.join('%d×%d' % a for a in ARMS), n_seeds, sum(nb for _, nb in ARMS)))
    _rng = check_arm_ranges()
    emit('[f6] seed 段（开跑前断言互不相交）：%s'
         % ', '.join('R=%d:[%d,%d]' % (r[2], r[0], r[1]) for r in _rng))
    for kk in chosen:
        cs = by_key[kk]
        emit('   %-22s 格=%2d %-9s %s' % (
            kk, len(cs), '+'.join(sorted({s for c in cs for s in c['strat'].split('+')})),
            ' '.join('%s·%s=%.3f%%/τ%.3f[%s]' % (c['crit'], c['inst'], c['rel'] * 100, c['tau'],
                                                 c['strat']) for c in cs)))
    if os.environ.get('F6_PREVIEW'):
        return 0

    fh = io.open(OUT, 'a', newline='', encoding='utf-8')
    w = csv.writer(fh)
    if os.path.getsize(OUT) == 0:
        w.writerow(HEAD)
        fh.flush()
    t_all, n_done = time.time(), 0
    for ki, kk in enumerate(chosen, 1):
        tid, et = kk.split('__')
        m = meta.get(kk) or {}
        path = os.path.join(ART, '%s.py' % kk)
        task = by_id.get(tid)
        strat = '+'.join(sorted({s for c in by_key[kk] for s in c['strat'].split('+')}))
        if task is None or not os.path.exists(path):
            w.writerow([kk, tid, m.get('template', ''), et, m.get('family', ''), 'MISSING',
                        '', '', '', '', HOR, '', '', '', strat, '', 'artifact or task missing'])
            fh.flush()
            continue
        t0, nblk = time.time(), 0
        for ai, (R, nb) in enumerate(ARMS):
            base = SEED0 + ai * ARM_STRIDE          # 逐臂分段，见 ARM_STRIDE 的注释
            for b in range(nb):
                if (kk, str(R), str(b)) in done:
                    continue
                ss = base + b * R
                obs, dt, note = C.run_artifact(path, R, HOR, 'none', ss)
                nblk += 1
                if obs is None:
                    w.writerow([kk, tid, m['template'], et, m['family'], 'CRASH', '',
                                R, b, ss, HOR, '', '', '', strat, '%.1f' % dt,
                                (note or '')[:120]])
                    fh.flush()
                    continue
                for crit, inst, rel, stt in judge(obs, task):
                    tau = TAU.get((m['template'], crit, inst))
                    if rel is None or tau is None:
                        w.writerow([kk, tid, m['template'], et, m['family'], crit, inst,
                                    R, b, ss, HOR, '', '' if tau is None else '%.6f' % tau,
                                    '', strat, '%.1f' % dt, (stt or 'no_tau')[:120]])
                        continue
                    w.writerow([kk, tid, m['template'], et, m['family'], crit, inst,
                                R, b, ss, HOR, '%.6e' % rel, '%.6f' % tau,
                                1 if rel > tau else 0, strat, '%.1f' % dt, (stt or '')[:60]])
                fh.flush()
        n_done += 1
        el = time.time() - t_all
        emit('[f6] %d/%d %s R=%s blocks=%d 本件 %.0fs 累计 %.1fmin 预计总 %.1fmin'
              % (ki, len(chosen), kk, strat, nblk, time.time() - t0, el / 60,
                 el / max(n_done, 1) * len(chosen) / 60))
    fh.close()
    emit('[f6] DONE 件=%d 总墙钟 %.1f min -> %s'
          % (n_done, (time.time() - t_all) / 60, OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
