"""变异体检出矩阵（腿 A 的主表原料）。

对 346 个"带已知标签的注入错型工件"逐个跑，用判分端 J1/J2/J3 打分，
把"理论预期(benign/detectable/weak/blind)"与"实测是否点火"对上。
这就是 K0 那 2x2 的放大版：K0 只验了取队规则一族，这里验整本错型目录。

预算口径：SEEDS/HORIZON 直接写进每一行，因为样本预算本身是本文的自变量（P2/P3），
不写预算的检出率没有意义。
逐条 flush、可续跑（已在 CSV 里出现过的 (task_id,error_type) 会跳过）。
"""
import os
import sys
import csv
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C  # noqa: E402
from inv_obs import j1_inv  # noqa: E402

ART = os.path.join(HERE, 'artifacts')
def _flat(x):
    s = str(x).replace(chr(10), ' | ').replace(chr(13), ' ')
    return s if len(s) <= 200 else s[:60] + ' ... ' + s[-140:]


def _row(vals):
    # 历史入口：CRASH 分支曾调用 _row，但函数从未定义；主表 0 崩溃所以一直没暴露。
    # 保留这个薄壳，让 CRASH 行与 MISSING 行同格式落盘。
    return vals

class _SanitizedWriter(object):
    def __init__(self, w):
        self._w = w
    def writerow(self, vals):
        self._w.writerow([('' if v is None else str(v).replace(chr(10), ' | ').replace(chr(13), ' '))
                          for v in vals])


OUT = os.path.join(HERE, 'MUTANT_MATRIX.csv')
MUT = os.path.join(HERE, 'mutants.jsonl')
SEEDS = int(os.environ.get('MM_SEEDS', 50))
HOR = float(os.environ.get('MM_HOR', 40000.0))
TAUS = ('0.01', '0.02', '0.03', '0.05')
HEAD = ['key', 'task_id', 'template', 'error_type', 'family', 'expected',
        'stage', 'instance', 'rel', 'seeds', 'horizon',
        'fired_0.01', 'fired_0.02', 'fired_0.03', 'fired_0.05', 'note']


def _sidecar(out):
    return os.path.splitext(out)[0] + '.committed'


def _fsync(fh):
    fh.flush()
    os.fsync(fh.fileno())


def csv_keys(out):
    """续跑键里**必须带 seeds**。
    原来只用 (task_id, error_type)：换个 MM_SEEDS 再跑，会因为键撞上而静默跳过所有行，
    于是"R=10 的矩阵"其实还是上次 R=50 的数 —— 这类静默失效比崩掉贵得多。"""
    s = set()
    if os.path.exists(out):
        with open(out, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                s.add((r['task_id'], r['error_type'], r['seeds'], r['horizon']))
    return s


def committed_keys(out):
    """块的提交标记。**不能拿 CSV 里出现过这个键当"跑完了"**：
    行是逐条写进同一个 append 句柄的，进程死在写块的循环里就留下一截半块，
    而半块里的前几行已经让这个键"出现过" ⇒ 续跑跳过它 ⇒ 那几格永久丢失且无人察觉。
    改为：整块写盘并 fsync 之后，才往边车追一行 key。"""
    p = _sidecar(out)
    if not os.path.exists(p):
        return None
    ks = set()
    with open(p, encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip(chr(10)).split(chr(9))
            if len(parts) == 4:
                ks.add(tuple(parts))
    return ks


def write_committed(out, keys):
    p = _sidecar(out)
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='') as f:
        for k in sorted(keys):
            f.write(chr(9).join(k) + chr(10))
        _fsync(f)
    os.replace(tmp, p)


def repair_partial(out, done):
    """把主表与 triggers 里没有提交标记的块删掉：它们是被 kill 打断的半块，接下来会重跑。"""
    rows_dropped, keys_dropped = 0, set()
    for path in (out, os.path.splitext(out)[0] + '.triggers.csv'):
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            continue
        with open(path, encoding='utf-8', newline='') as f:
            rd = csv.DictReader(f)
            head = rd.fieldnames
            if not head:
                continue
            rows = list(rd)
        keep, bad = [], set()
        for r in rows:
            k = (r['task_id'], r['error_type'], r['seeds'], r['horizon'])
            if k in done:
                keep.append(r)
            else:
                bad.add(k)
        if not bad:
            continue
        tmp = path + '.repair.tmp'
        with open(tmp, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=head)
            w.writeheader()
            w.writerows(keep)
            _fsync(f)
        os.replace(tmp, path)
        rows_dropped += len(rows) - len(keep)
        keys_dropped |= bad
    return rows_dropped, keys_dropped


def fired_cols(d):
    fa = d.get('fired_at') or {}
    return [1 if fa.get(t) else (0 if t in fa else '') for t in TAUS]


def main():
    global OUT          # --out= 换文件；续跑键里也带 seeds，所以换预算不会被旧文件吞掉
    shard, nshard = 1, 1
    out_override = None
    skip_file = None
    for a in sys.argv[1:]:
        if a.startswith('--out='):
            out_override = a.split('=', 1)[1]
        elif a.startswith('--skip-file='):
            skip_file = a.split('=', 1)[1]
        elif a.startswith('--shard='):
            shard, nshard = [int(x) for x in a.split('=')[1].split('/')]
    if out_override:
        OUT = out_override if os.path.isabs(out_override) else os.path.join(HERE, out_override)
    ms = [json.loads(l) for l in open(MUT, encoding='utf-8')]
    by_id = {t['task_id']: t for t in C.load_tasks()}
    done = committed_keys(OUT)
    if done is None and os.path.exists(OUT):
        # 旧表没有边车：按"表里已有的键都算提交过"接管，否则第一次续跑会把整张主表重做一遍。
        done = csv_keys(OUT)
        write_committed(OUT, done)
        print('[mmatrix %d/%d] 旧表接管：%d 个键视为已提交（无半块可判，按完整块信任）'
              % (shard, nshard, len(done)), flush=True)
    done = done or set()
    dropped, dkeys = repair_partial(OUT, done)
    if dropped:
        print('[mmatrix %d/%d] 修复半块：删掉 %d 行 / %d 个未提交块，接下来重跑它们'
              % (shard, nshard, dropped, len(dkeys)), flush=True)
    skip = set(done)
    if skip_file:                     # 允许把别的分片当成已完成清单，只补差集
        sp = skip_file if os.path.isabs(skip_file) else os.path.join(HERE, skip_file)
        for r in csv.DictReader(open(sp, encoding='utf-8')):
            skip.add((r['task_id'], r['error_type'], r['seeds'], r['horizon']))
    only = os.environ.get('MM_ONLY')  # 逗号分隔的 error_type 白名单，用来单独处理慢件
    if only:
        onlyset = set(only.split(','))
    key = lambda m: (m['task_id'], m['error_type'], str(SEEDS), str(HOR))
    # 分片必须在「跳过已完成」之前定：否则续跑会重新切分剩余列表，
    # 同一件可能被两个分片各跑一次、或被两个分片都漏掉（10-29 实测 B 里多跑 eoq-02 就是它）。
    partition = list(ms)
    if os.environ.get('MM_SKIP'):
        bad = set(os.environ['MM_SKIP'].split(','))
        partition = [m for m in partition if (m['task_id'], m['error_type']) not in bad]
    # 这个开关上一版只读了环境变量、从不过滤：设了 MM_ONLY 也照跑全量，注释却在说"白名单"。
    # 静默不生效比没有这个开关更贵——按它排的机时会全部落空。
    if only:
        partition = [m for m in partition if m['error_type'] in onlyset]
    mine = partition[(shard - 1)::nshard]
    todo = [m for m in mine if key(m) not in skip]
    # 续跑键必须真的能用：键格式一旦和 done_keys() 不一致，这里会静默地「谁都跳过不了」，
    # 于是重跑变成重做、合并时全是重复行。今天真的踩到过。
    if skip and len(todo) == len(mine) and mine:
        raise SystemExit('续跑键失效：skip 有 %d 条却没跳过本分片任何件 ⇒ 键格式与 done_keys 不一致' % len(skip))
    new = not os.path.exists(OUT)
    fh = open(OUT, 'a', newline='', encoding='utf-8')
    w = _SanitizedWriter(csv.writer(fh))
    if new:
        w.writerow(HEAD)
        fh.flush()

    # 触发计数随表落盘（P-02/P-03）：恒等类/漏检的**身份**要由"机制有没有真跑"决定，
    # 而不是由"数是不是和参照件一样"猜——后者把 M/D/1 的路径恒等（机制跑了 11 万次、读数逐位不变）
    # 误判成注入空转。一片一文件，避免并发追加把对方行盖掉。
    TRIG = os.path.splitext(OUT)[0] + '.triggers.csv'
    tfh = open(TRIG, 'a', newline='', encoding='utf-8')
    tw = _SanitizedWriter(csv.writer(tfh))
    if not os.path.exists(TRIG) or os.path.getsize(TRIG) == 0:
        tw.writerow(['key', 'task_id', 'error_type', 'template', 'family', 'expected',
                     'seeds', 'horizon', 'trig_nonhead', 'trig_preempt', 'trig_class0',
                     'trig_transfer', 'trig_swap_noop', 'trig_leak', 'trig_fieldconst',
                     'trig_backsolve', 'trig_lostcycle', 'ran'])
        tfh.flush()

    def trig_row(kk, mm, ob):
        vals = [kk, mm['task_id'], mm['error_type'], mm['template'], mm['family'],
                mm['expected'], SEEDS, HOR]
        for nm in ('trig_nonhead', 'trig_preempt', 'trig_class0', 'trig_transfer',
                   'trig_swap_noop', 'trig_leak', 'trig_fieldconst', 'trig_backsolve',
                   'trig_lostcycle'):
            vals.append('' if ob is None else ob.get(nm))
        vals.append('' if ob is None else '1')
        return vals

    dfh = open(_sidecar(OUT), 'a', newline='', encoding='utf-8')

    def emit(rows, kk, trig):
        """一个块 = 主表若干行 + 一行 triggers + 一行提交标记。
        落盘顺序固定：先把块里所有行写进主表并 fsync，再写 triggers，最后追提交标记。
        死在任意一步，这个块都没有提交标记，续跑时 repair_partial 会把它整块删掉重跑。"""
        for r in rows:
            w.writerow(r)
        _fsync(fh)
        tw.writerow(trig)
        _fsync(tfh)
        dfh.write(chr(9).join(kk) + chr(10))
        _fsync(dfh)

    print('[mmatrix %d/%d] todo=%d skip=%d seeds=%d hor=%g'
          % (shard, nshard, len(todo), len(skip), SEEDS, HOR), flush=True)
    n = 0
    for m in todo:
        tid, et = m['task_id'], m['error_type']
        key = '%s__%s' % (tid, et)
        kk = (tid, et, str(SEEDS), str(HOR))
        path = os.path.join(ART, '%s__%s.py' % (tid, et))
        n += 1
        if not os.path.exists(path):
            emit([[key, tid, m['template'], et, m['family'], m['expected'],
                   'MISSING', '', '', SEEDS, HOR, '', '', '', '', 'artifact not on disk']],
                 kk, trig_row(key, m, None))
            continue
        task = by_id[tid]
        obs, dt, note = C.run_artifact(path, SEEDS, HOR, 'none', 1)
        if obs is None:
            # 运行期失败单独立一档，但 **fired_* 一律留空**：
            # 上一版在这里硬写 1,1,1,1，于是"崩了"和"判据在 τ 上点火"变成同一个数，
            # 汇总时把 15 件"根本没吐出数字"的注入件算进了判据的分数。
            emit([_row([key, tid, m['template'], et, m['family'], m['expected'],
                        'CRASH', 'runtime', '', SEEDS, HOR, '', '', '', '', note])],
                 kk, trig_row(key, m, None))
            continue
        rows = []
        j1 = C.j1_analytic(obs, task, tau=None)
        for o, d in j1['per_obs'].items():
            rel = d.get('rel')
            rows.append([key, tid, m['template'], et, m['family'], m['expected'],
                         'J1', o, ('%.6f' % rel if rel is not None else ''), SEEDS, HOR]
                        + fired_cols(d) + [d.get('status', '')[:120]])
        for o, d in j1_inv(obs, task).items():        # 报童/EOQ 走这套观测量，否则会静默消失
            rel = d.get('rel')
            rows.append([key, tid, m['template'], et, m['family'], m['expected'],
                         'J1inv', o, ('%.6f' % rel if rel is not None else ''), SEEDS, HOR]
                        + fired_cols(d) + [d.get('status', '')[:120]])
        for cname, fn in (('J2', C.j2_conservation), ('J3', C.j3_pairing)):
            res = fn(obs, task, tau=None)
            for k2, d in (res.get('per_stat') or {}).items():
                rel = d.get('rel')
                rows.append([key, tid, m['template'], et, m['family'], m['expected'],
                             cname, k2, ('%.6e' % rel if rel is not None else ''), SEEDS, HOR]
                            + fired_cols(d) + [d.get('status', '')[:120]])
        if not rows:
            rows.append([key, tid, m['template'], et, m['family'], m['expected'],
                         'NOINSTANCE', '', '', SEEDS, HOR, '', '', '', '', '该件无任何可判实例'])
        emit(rows, kk, trig_row(key, m, obs))
        if n % 5 == 0 or n == 1:
            print('[mmatrix %d/%d] %d/%d %s %.1fs rows=%d' % (shard, nshard, n, len(todo),
                                                              key, dt, len(rows)), flush=True)
    fh.close()
    tfh.close()
    dfh.close()
    print('[mmatrix %d/%d] ALL %d done' % (shard, nshard, n), flush=True)


if __name__ == '__main__':
    main()
