"""S3：kill/restart 实测。对一个 7 件的分片，在四个时刻 SIGKILL（TerminateProcess），
重启后续跑，逐格比对是否与不间断基线完全一致；再做一次注入式半块（截断 4 行 + 抽掉提交标记），
验证 repair_partial 会把整块删掉重跑，而不是把它当成已完成。

输出 S3_KILL_RESULT.md 与 killtest.json。
"""
import csv
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable
ENV = dict(os.environ)
ENV.update(MM_SEEDS='10', MM_HOR='40000', PYTHONIOENCODING='utf-8')
SHARD = '1/60'


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def fp(rows):
    """指纹：每个 (task, err) 块的完整行集合，行内所有字段排序后比较。"""
    g = {}
    for r in rows:
        k = (r['task_id'], r['error_type'])
        g.setdefault(k, []).append(tuple(sorted(r.items())))
    return {k: sorted(v) for k, v in g.items()}


def committed(out):
    p = os.path.splitext(out)[0] + '.committed'
    if not os.path.exists(p):
        return []
    return [l.rstrip('\n') for l in open(p, encoding='utf-8') if l.strip()]


def start(out, tag):
    log = open(os.path.join(os.path.dirname(out), 'run_%s.log' % tag), 'a', encoding='utf-8')
    return subprocess.Popen([PY, 'run_mutant_matrix.py', '--out=' + out, '--shard=' + SHARD],
                            cwd=ROOT, env=ENV, stdout=log, stderr=subprocess.STDOUT)


def wait(p):
    p.wait()
    return p.returncode


def trial(name, kill_after, base_fp, base_rows):
    d = os.path.join(HERE, name)
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, 'run.csv')
    for pth in (out, os.path.splitext(out)[0] + '.committed',
                os.path.splitext(out)[0] + '.triggers.csv',
                os.path.join(d, 'run_1.log'), os.path.join(d, 'run_2.log')):
        if os.path.exists(pth):
            os.remove(pth)
    rec = {'trial': name, 'kill_after_s': kill_after}
    t0 = time.time()
    p = start(out, '1')
    time.sleep(kill_after)
    p.kill()                       # TerminateProcess：不给 flush 机会
    p.wait()
    rec['kill_at_s'] = round(time.time() - t0, 1)
    rec['rows_at_kill'] = len(load(out))
    rec['committed_at_kill'] = len(committed(out))
    rec['blocks_committed'] = [tuple(l.split('\t'))[:2] for l in committed(out)]
    t1 = time.time()
    p2 = start(out, '2')
    rc = wait(p2)
    rec['resume_rc'] = rc
    rec['resume_s'] = round(time.time() - t1, 1)
    rows = load(out)
    rec['rows_final'] = len(rows)
    rec['keys_final'] = len(fp(rows))
    rec['identical'] = (fp(rows) == base_fp)
    rec['duplicate_rows'] = len(rows) - len(load(os.path.join(HERE, 'base.csv')))
    txt = open(os.path.join(d, 'run_2.log'), encoding='utf-8', errors='replace').read()
    rec['resume_todo'] = [l for l in txt.splitlines() if 'todo=' in l]
    rec['repair_line'] = [l for l in txt.splitlines() if '修复半块' in l]
    return rec


def partial_block_trial(base_rows):
    """注入式半块：把最后一块的末 4 行截掉，并从提交标记里抽掉这个键。
    这模拟"进程死在写块的循环里、行已部分落盘"——真实 kill 由于缓冲很少命中这个微秒窗口。"""
    d = os.path.join(HERE, 'inject_partial')
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, 'run.csv')
    for pth in (out, os.path.splitext(out)[0] + '.committed',
                os.path.splitext(out)[0] + '.triggers.csv',
                os.path.join(d, 'run_1.log')):
        if os.path.exists(pth):
            os.remove(pth)
    rows = load(os.path.join(HERE, 'base.csv'))
    last_key = rows[-1]['task_id'], rows[-1]['error_type']
    keep = [r for r in rows if (r['task_id'], r['error_type']) != last_key]
    cut = [r for r in rows if (r['task_id'], r['error_type']) == last_key][:-4]
    with open(out, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(keep + cut)
    side = os.path.join(d, 'run.committed')
    with open(side, 'w', encoding='utf-8') as f:
        for k in committed(os.path.join(HERE, 'base.csv')):
            if not k.startswith(last_key[0] + '\t' + last_key[1] + '\t'):
                f.write(k + '\n')
    rec = {'trial': 'inject_partial', 'truncated_key': '%s__%s' % last_key,
           'rows_injected': len(keep) + len(cut), 'missing_rows': 4}
    p = start(out, '1')
    rec['rc'] = wait(p)
    after = load(out)
    rec['identical'] = (fp(after) == fp(base_rows))
    rec['rows_final'] = len(after)
    txt = open(os.path.join(d, 'run_1.log'), encoding='utf-8', errors='replace').read()
    rec['repair_line'] = [l for l in txt.splitlines() if '修复半块' in l]
    rec['todo_line'] = [l for l in txt.splitlines() if 'todo=' in l]
    return rec


def main():
    base = load(os.path.join(HERE, 'base.csv'))
    bfp = fp(base)
    print('baseline: %d rows, %d blocks' % (len(base), len(bfp)), flush=True)
    recs = []
    for k in (8, 20, 35, 50):
        r = trial('kill_%02d' % k, k, bfp, base)
        print(json.dumps(r, ensure_ascii=False), flush=True)
        recs.append(r)
    r = partial_block_trial(base)
    print(json.dumps(r, ensure_ascii=False), flush=True)
    recs.append(r)
    with open(os.path.join(HERE, 'killtest.json'), 'w', encoding='utf-8') as f:
        json.dump(recs, f, ensure_ascii=False, indent=1)
    ok = sum(1 for r in recs if r.get('identical'))
    print('IDENTICAL %d/%d' % (ok, len(recs)))


if __name__ == '__main__':
    main()
