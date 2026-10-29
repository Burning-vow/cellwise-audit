"""Strong-scaling measurement for the audit workload.

Fixed workload = a deterministic stratified sample of mutant artifacts, all at
R=10 / horizon 40,000. For each worker count P we re-run the same list and
record the makespan. Resumable: a P level already present in the summary is
skipped.

Usage:
  python STRONG_SCALING.py --n=256 --ps=1,2,4,8,16
"""
import os, sys, csv, json, time, argparse, statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(HERE)
sys.path.insert(0, BENCH)
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

import criteria as C

SEEDS, HOR = 10, 40000
# artifacts with a known heavy tail, kept in the sample whatever the stride is
FORCE = ['md1-05__e12.py', 'mmc-04__e03.py', 'mmc-04__e02.py', 'mmc-04__e13.py',
         'jackson2-06__e27.py', 'mh2-01__e03.py']


def sample(n):
    rows = [json.loads(l) for l in open(os.path.join(BENCH, 'mutants.jsonl'), encoding='utf-8')]
    seen, out = set(), []
    artdir = os.path.join(BENCH, 'artifacts')
    for r in rows:
        name = os.path.basename(r.get('artifact_path') or '')
        if not name or name in seen:
            continue
        path = os.path.join(artdir, name)
        if not os.path.exists(path):
            continue
        seen.add(name)
        out.append((r['template'], r['task_id'], r['error_type'], path))
    out.sort()
    if len(out) <= n:
        return out
    stride = len(out) / float(n)
    picked, idx = [], {int(i * stride) for i in range(n)}
    for i, row in enumerate(out):
        if i in idx:
            picked.append(row)
    have = {os.path.basename(r[3]) for r in picked}
    for f in FORCE:
        if f.lower() not in {h.lower() for h in have}:
            for row in out:
                if os.path.basename(row[3]).lower() == f.lower():
                    picked.append(row)
                    break
    return sorted(set(picked))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=256)
    ap.add_argument('--ps', default='1,2,4,8,16')
    ap.add_argument('--tag', default='main')
    a = ap.parse_args()
    ps = [int(x) for x in a.ps.split(',')]
    todo = sample(a.n)
    if not todo:
        print('[scaling] empty workload -- check artifact paths', flush=True)
        return
    outdir = HERE
    run_csv = os.path.join(outdir, f'scaling_runs_{a.tag}.csv')
    sum_csv = os.path.join(outdir, f'scaling_summary_{a.tag}.csv')
    print(f'[scaling] workload={len(todo)} artifacts, P in {ps}', flush=True)

    done = set()
    if os.path.exists(sum_csv):
        for r in csv.DictReader(open(sum_csv, encoding='utf-8')):
            done.add(int(r['workers']))

    new_run = not os.path.exists(run_csv)
    if new_run:
        with open(run_csv, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(['workers', 'artifact', 'wall_s', 'start_off_s', 'end_off_s', 'note'])
    new_sum = not os.path.exists(sum_csv)
    if new_sum:
        with open(sum_csv, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(['workers', 'n', 'makespan_s', 'sum_wall_s', 'ideal_speedup',
                                    'speedup', 'efficiency', 'max_wall_s', 'mean_wall_s'])
    for P in ps:
        if P in done:
            print(f'[scaling] P={P} already done, skip', flush=True)
            continue
        t0 = time.time()
        rows = []
        # rows are flushed one by one: a killed level still leaves usable data
        with open(run_csv, 'a', newline='', encoding='utf-8') as frow:
            wr = csv.writer(frow)
            with ThreadPoolExecutor(max_workers=P) as ex:
                futs = {ex.submit(run_one, r): r for r in todo}
                for fu in as_completed(futs):
                    r = fu.result()
                    rows.append(r)
                    wr.writerow([P, r[0], '%.3f' % r[2], '%.3f' % r[3], '%.3f' % r[4], r[5]])
                    frow.flush()
        span = time.time() - t0
        walls = [r[2] for r in rows]
        with open(sum_csv, 'a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow([P, len(rows), '%.2f' % span, '%.1f' % sum(walls), '',
                        '', '', '%.2f' % max(walls), '%.2f' % statistics.mean(walls)])
            f.flush()
        print(f'[scaling] P={P} n={len(rows)} makespan={span:.1f}s '
              f'sum_wall={sum(walls):.0f}s max={max(walls):.1f}s mean={statistics.mean(walls):.1f}s',
              flush=True)
    # fill speedup columns once all P levels exist
    fill_speedups(sum_csv)
    print('[scaling] done', flush=True)


def run_one(row):
    t = time.time()
    try:
        obs, dt, note = C.run_artifact(row[3], SEEDS, HOR, 'none', 1)
    except Exception as e:                                    # keep going; a crash is data too
        dt, note = -1.0, 'EXC:%s' % type(e).__name__
    return (os.path.basename(row[3]), row[2], float(dt), t, time.time(), note[:60])


def fill_speedups(path):
    rows = list(csv.DictReader(open(path, encoding='utf-8')))
    if not rows:
        return
    by = {int(r['workers']): r for r in rows}
    if 1 not in by:
        return
    t1 = float(by[1]['makespan_s'])
    for P, r in by.items():
        r['ideal_speedup'] = '%.2f' % P
        r['speedup'] = '%.2f' % (t1 / float(r['makespan_s']))
        r['efficiency'] = '%.3f' % (t1 / float(r['makespan_s']) / P)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for P in sorted(by):
            w.writerow(by[P])


if __name__ == '__main__':
    main()
