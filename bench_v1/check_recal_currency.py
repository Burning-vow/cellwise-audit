"""探针：现在的 simcore+criteria 出口，和 RECAL64_raw.jsonl（10-17 06:38 测的）逐字段对账。

为什么要它：`simcore.py` 的 mtime 是 10:12，而 `table_tau_v2.csv`/`table_FP_v2.csv`（09:53）
是从 06:38 的 raw 聚合出来的 ⇒ **标定表比发射器旧**。腿 B 要用这套阈值判 LLM 写的工件，
所以"06:38 之后 simcore 的改动会不会改变 REF 报出来的残差"必须实测回答，不许靠我读 diff 推理。

比什么：不比 obs 全字典（raw 里没存 obs，只存了 `rel`），而是**用 run_recal64.measure() 原函数**
把新 obs 折算成同一套 `rel` 键，再与 raw 里那条 task 级 ss=1 的 `rel` 逐键比。
口径也照抄（seeds=10、horizon=40000、purpose=none、seed_start=1），所以应当**逐位相等**。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C          # noqa: E402
import run_recal64 as R       # noqa: E402  复用它的 measure()，避免我自己重新发明一遍口径

ART = os.path.join(HERE, 'artifacts')
OUT = os.path.join(HERE, 'RECAL_CURRENCY.csv')


def main():
    stored,basis_bad = {}, []
    for line in io.open(R.RAW, encoding='utf-8'):
        if not line.strip():
            continue
        d = json.loads(line)
        if d.get('purpose') == 'task' and d.get('seed_start') == 1 and 'rel' in d:
            # 每一行**自带的口径**必须等于本次要用的口径，否则"逐位相等"是拿两个预算比出来的
            if (d.get('seeds'), d.get('horizon')) != (R.SEEDS_T, R.HOR):
                basis_bad.append((d['task_id'], d.get('seeds'), d.get('horizon')))
            stored[d['task_id']] = d['rel']
    if basis_bad:
        raise SystemExit('raw 里有 %d 行的 seeds/horizon 与当前口径(%d,%g)不符：%s '
                         '⇒ 先按当前口径重跑 run_recal64，不许跨预算比逐位' % (
                             len(basis_bad), R.SEEDS_T, R.HOR, basis_bad[:4]))
    tasks = [t for t in C.load_tasks() if os.path.exists(os.path.join(ART, '%s__REF.py' % t['task_id']))]
    # 分母必须是题集全量：以前少几个 REF 就报"题=6 逐位全等=6"再退出码 0（审计 P-08）
    n_all = sum(1 for l in io.open(os.path.join(HERE, 'tasks.jsonl'), encoding='utf-8') if l.strip())
    assert len(tasks) == n_all, ('有题没有参照件工件：题集 %d 题、能跑的 %d 题 ⇒ 缺 %s' % (
        n_all, len(tasks), sorted({t['task_id'] for t in C.load_tasks()} -
                                  {t['task_id'] for t in tasks})[:8]))
    assert len(stored) == n_all, 'raw 里只有 %d 题的历史行，题集有 %d 题 ⇒ 标定表覆盖不全' % (
        len(stored), n_all)
    print('题=%d 有历史行=%d  口径 seeds=%d hor=%g' % (len(tasks), len(stored), R.SEEDS_T, R.HOR), flush=True)
    # 先写 .tmp，跑完再原子改名。原因（2026-10-19 我自己造的事故）：
    # 就地 `open(OUT,'w')` 会先把上一版好文件截断，中途被杀就只剩半份
    # （那次把 64 行全 IDENTICAL 的结果截成 12 行）。半份文件比没有文件更坏——
    # 它看起来像证据。
    TMP = OUT + '.tmp'
    fh = io.open(TMP, 'w', encoding='utf-8', newline='')
    fh.write('task_id,status,n_key_diff,n_val_diff,detail\n')
    n_ok = n_bad = n_skip = 0
    tot = 0.0
    for t in tasks:
        tid = t['task_id']
        if tid not in stored:
            fh.write('%s,NO_STORED_ROW,,,\n' % tid)
            fh.flush()
            n_skip += 1
            continue
        obs, dt, note = C.run_artifact(os.path.join(ART, '%s__REF.py' % tid), R.SEEDS_T, R.HOR, 'none', 1)
        tot += dt
        if obs is None:
            fh.write('%s,RUN_FAIL,,,%s\n' % (tid, str(note)[-120:].replace(',', ';')))
            fh.flush()
            n_bad += 1
            print('%-16s RUN_FAIL %s' % (tid, str(note)[-60:]), flush=True)
            continue
        new = {'%s|%s' % k: v for k, v in R.measure(obs, t).items()}
        old = stored[tid]
        only_new = sorted(set(new) - set(old))
        only_old = sorted(set(old) - set(new))
        diffs = []
        for k in sorted(set(new) & set(old)):
            a, b = new[k], old[k]
            if a != b and not (isinstance(a, float) and isinstance(b, float) and a != a and b != b):
                diffs.append('%s:%.6g->%.6g' % (k, b, a))
        # ⚠ 加了新判据（如 J0）以后，raw 里没有那些键 ⇒ `only_new` 必然非空。
        #    把它判成 DRIFT 就等于"每加一条判据，全部 64 题一起变红"，
        #    于是大家会去把闸调松 —— 那是最坏的修法。新增键 = 可见但不阻断；
        #    **值变了或旧键消失**才阻断。
        status = ('IDENTICAL' if not (only_old or diffs)
                  else ('IDENTICAL_NEWKEYS' if not diffs and not only_old and only_new else 'DRIFT'))
        fh.write('%s,%s,%d,%d,%s\n' % (tid, status, len(only_new) + len(only_old), len(diffs),
                  ';'.join(['+' + ','.join(only_new), '-' + ','.join(only_old),
                            '=' + ';'.join(diffs)])[:500].replace(',', ';')))
        fh.flush()
        if status.startswith('IDENTICAL'):
            n_ok += 1
        else:
            n_bad += 1
        print('%-16s %-9s 键差=%d 值差=%d  %.0fs  累计=%.0fs' % (
            tid, status, len(only_new) + len(only_old), len(diffs), dt, tot), flush=True)
    fh.close()
    os.replace(TMP, OUT)          # 原子替换：只有跑完才让新文件可见
    print('\n合计 题=%d 逐位全等=%d 有漂移=%d 无历史行=%d  机时=%.1f 分钟  明细 -> %s' % (
        len(tasks), n_ok, n_bad, n_skip, tot / 60.0, OUT))
    return 0 if n_bad == 0 and n_skip == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
