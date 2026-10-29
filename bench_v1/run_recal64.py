"""在 **artifacts 出口**上重标 64 题的 τ*（产出 table_tau_v2.csv / table_FP_v2.csv）。

为什么要重标（不是闲着没事）：
  Step 2 的 table_tau.csv 是在 `calib_ref/*__REF.py` 这条出口上标定的，
  而腿 B 真正要判的是 `artifacts/*__REF.py` 这条出口。今晚已经实测证明两条出口会在
  同名字段上给不同定义（mmcK 的 busy_frac：一条报 E[min(N,c)]/c、一条报 1−π0），
  ⇒ 用 A 出口的噪声尺度去判 B 出口的工件，阈值就是错的。
  这一版把 64 题全部按 artifacts 出口重标，顺带把 26 道以前没有行的题补进来。

口径与 Step 2 保持一致（同一 GRID、同一 Wilson、同一 R1/R2/R3 选档规则）：
  task 级试验 = 一次工件调用（seeds=10，每 10 个种子换一段窗口），共 10 次 ⇒ 每题 10 个独立试验
  batch 级试验 = 一次 seeds=100 的调用，把 per_seed_* 切成 10 个批，按批均值法算统计量
  R1 task 级 Wilson 上界 ≤ 5%；R2 task 级零报警且 batch 级上界 ≤ 5%；R3 只报"零报警最小 τ"
逐条 flush、可续跑（RECAL64_raw.jsonl 里已有的 (task,purpose,seed_start) 会跳过）。
"""
import json
import os
import sys
import csv
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C  # noqa: E402
from inv_obs import j1_inv  # noqa: E402

ART = os.path.join(HERE, 'artifacts')
# 可以指到别的文件：4 个分片并行时**必须**各写各的（并发 append 同一份 jsonl 会咬出半行），
# 跑完再合并。合并前逐行数记录、按 (task,purpose,seed_start) 查重，缺一条就停下。
RAW = os.environ.get('RECAL_RAW') or os.path.join(HERE, 'RECAL64_raw.jsonl')
GRID = C.TAU_GRID
TARGET = C.WILSON_TARGET_UPPER
NTRIAL = 10
SEEDS_T = 10
SEEDS_B = 100
HOR = 40000.0
J1_OBS = ('W', 'L', 'p_loss', 'busy_frac', 'p_wait', 'q', 'exp_profit', 'cost')


def measure(obs, task):
    """一次观测 -> {('J1', obs): rel, ('J2', key): rel, ('J3', key): rel}"""
    out = {}
    for o, d in C.j1_analytic(obs, task, tau=None)['per_obs'].items():
        if d.get('rel') is not None:
            out[('J1', o)] = d['rel']
    for o, d in j1_inv(obs, task).items():
        if d.get('rel') is not None:
            out[('J1', o)] = d['rel']
    # J0 自报口径自洽（`horizon` 是**调用参数**，J0e 那条腿靠它才改不掉）
    for cn, fn in (('J0', lambda o, t, tau=None: C.j0_unit_anchor(o, t, tau=tau, horizon=HOR)),
                   ('J2', C.j2_conservation), ('J3', C.j3_pairing)):
        for k, d in (fn(obs, task, tau=None).get('per_stat') or {}).items():
            if d.get('rel') is not None:
                out[(cn, k)] = d['rel']
    return out


def batch_alarms(obs, task):
    """把 per_seed_* 切批，算每批统计量（batch 级试验，给 R2 用）。"""
    res = {}
    truth = task.get('truth_print') or {}
    for o in J1_OBS:
        ps = obs.get('per_seed_%s' % o)
        if not ps or truth.get(o) is None:
            continue
        nb = max(1, len(ps) // SEEDS_T)
        vals = []
        for b in range(nb):
            chunk = ps[b * SEEDS_T:(b + 1) * SEEDS_T]
            if len(chunk) < 2:
                continue
            vals.append(C.rel_dev(sum(chunk) / len(chunk), truth[o]))
        if vals:
            res[('J1', o)] = vals
    return res


def main():
    shard, nshard = 1, 1
    for a in sys.argv[1:]:
        if a.startswith('--shard='):
            shard, nshard = [int(x) for x in a.split('=')[1].split('/')]
        else:
            # 严格解析：认不出的参数直接停下。静默吞参数最坏的地方在于它会把
            # "我以为我在跑 4 个分片"变成"4 个进程全在跑同一份全量"，而输出看起来正常。
            raise SystemExit('不认识的参数 %r（只支持 --shard=i/n）' % a)
    if not (1 <= shard <= nshard):
        raise SystemExit('--shard=%d/%d 非法' % (shard, nshard))
    # 口径回显：跨进程的参数必须打印出来让人对账，不然产物里的 seeds/horizon 无人验证
    print('[recal 参数回显] shard=%d/%d RAW=%s SEEDS_T=%d NTRIAL=%d SEEDS_B=%d HOR=%g'
          % (shard, nshard, RAW, SEEDS_T, NTRIAL, SEEDS_B, HOR), flush=True)
    done = set()
    if os.path.exists(RAW):
        for line in open(RAW, encoding='utf-8'):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            done.add((d['task_id'], d['purpose'], d['seed_start']))
    tasks = [t for t in C.load_tasks()
             if os.path.exists(os.path.join(ART, '%s__REF.py' % t['task_id']))]
    tasks = tasks[(shard - 1)::nshard]
    fh = open(RAW, 'a', encoding='utf-8')
    t0 = time.time()
    print('[recal %d/%d] tasks=%d done_rows=%d' % (shard, nshard, len(tasks), len(done)), flush=True)
    for t in tasks:
        tid = t['task_id']
        path = os.path.join(ART, '%s__REF.py' % tid)
        for i in range(NTRIAL):
            ss = 1 + i * SEEDS_T
            if (tid, 'task', ss) in done:
                continue
            obs, dt, note = C.run_artifact(path, SEEDS_T, HOR, 'none', ss)
            rec = {'task_id': tid, 'template': t['template'], 'purpose': 'task',
                   'seed_start': ss, 'seeds': SEEDS_T, 'horizon': HOR, 'wall': round(dt, 1)}
            if obs is None:
                rec['error'] = str(note)[-160:]
            else:
                rec['rel'] = {'%s|%s' % k: v for k, v in measure(obs, t).items()}
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
            fh.flush()
        if (tid, 'batch', 1) not in done:
            obs, dt, note = C.run_artifact(path, SEEDS_B, HOR, 'none', 1)
            rec = {'task_id': tid, 'template': t['template'], 'purpose': 'batch',
                   'seed_start': 1, 'seeds': SEEDS_B, 'horizon': HOR, 'wall': round(dt, 1)}
            if obs is None:
                rec['error'] = str(note)[-160:]
            else:
                rec['batches'] = {'%s|%s' % k: v for k, v in batch_alarms(obs, t).items()}
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
            fh.flush()
        print('[recal %d/%d] %s done  %.0fs elapsed' % (shard, nshard, tid, time.time() - t0), flush=True)
    fh.close()


if __name__ == '__main__':
    main()
