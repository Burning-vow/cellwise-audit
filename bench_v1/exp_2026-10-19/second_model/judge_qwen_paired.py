# -*- coding: utf-8 -*-
"""Qwen vs flash：严格同 20 题配对（20 题 × 3 抽 = 60 vs 60）。

输出：QWEN_vs_FLASH_20TASKS.md / .csv
口径：两边都走 rejudge_existing（420s / R=10 / 40000）；Qwen 的 TRUNCATED 取生成侧 manifest，
flash 的 TRUNCATED 取 legB 生成侧 manifest（finish=length / err 含 TRUNCATED），与判定侧分型并列。
"""
import csv
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
BENCH = os.path.dirname(EXP)
sys.path.insert(0, BENCH)
sys.path.insert(0, HERE)
import LEGB_ARMS3 as A          # noqa: E402
import rejudge_existing as R    # noqa: E402
import gen_qwen as GQ           # noqa: E402

QWEN_DIR = os.path.join(HERE, 'qwen3.8flash_20261019')
FLASH_DIR = os.path.join(BENCH, 'legB', 'flash20261018')
QWEN_SIDES = sorted(glob.glob(os.path.join(QWEN_DIR, '_qwen_shard*.tsvl')))
FLASH_SIDE = os.path.join(BENCH, '_rejudge_flash20261018_v2.txt')
QWEN_MAN = os.path.join(QWEN_DIR, 'manifest.jsonl')
FLASH_MAN = os.path.join(BENCH, 'legB', 'legB_flash20261018.jsonl')
OUT_MD = os.path.join(HERE, 'QWEN_vs_FLASH_20TASKS.md')
OUT_CSV = os.path.join(HERE, 'QWEN_vs_FLASH_20TASKS.csv')

IDS = set(GQ.pick_20())
QWEN = [r for r in R.load_sidecars(QWEN_SIDES) if r.get('task_id') in IDS]
FLASH = [r for r in A.load(FLASH_SIDE) if r.get('task_id') in IDS]
assert len(QWEN) == 60 and len(FLASH) == 60, (len(QWEN), len(FLASH))


def stats(rs):
    return A.stats(rs)


def closed_event(rs):
    closed = [r for r in rs if r.get('template') in ('eoq', 'newsvendor')]
    event = [r for r in rs if r.get('template') not in ('eoq', 'newsvendor')]
    return stats(closed), stats(event)


def truncated(rs, man_path, qwen=False):
    man = {}
    for line in io.open(man_path, encoding='utf-8'):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        key = r.get('artifact') if qwen else r.get('file')
        if key:
            man[key] = r
    out = []
    for r in rs:
        m = man.get(r.get('file'))
        if not m:
            continue
        err = str(m.get('err') or '')
        fin = str(m.get('finish') or '')
        if 'TRUNCATED' in err or fin == 'length':
            out.append(r)
    return out


def j2a_vals(rs):
    vals = []
    for r in rs:
        for line in (r.get('cells') or []):
            if 'J2a' in line:
                m = re.search(r'rel=([0-9.eE+\-]+)', line)
                if m:
                    try:
                        vals.append(float(m.group(1)))
                    except ValueError:
                        pass
    return vals


def wl_hits(rs, d):
    hit = n = 0
    for r in rs:
        p = os.path.join(d, r.get('file') or '')
        if not os.path.exists(p):
            continue
        n += 1
        code = io.open(p, encoding='utf-8', errors='ignore').read()
        if re.search(r'\bW\s*=\s*L\s*/', code):
            hit += 1
    return hit, n


def pct(a, b):
    return '—' if not b else '%.1f%%' % (100.0 * a / b)


def line(name, f, q):
    return '| %s | %s | %s |' % (name, f, q)


def main():
    fs, qs = stats(FLASH), stats(QWEN)
    fc, fe = closed_event(FLASH)
    qc, qe = closed_event(QWEN)
    ftr = truncated(FLASH, FLASH_MAN, qwen=False)
    qtr = truncated(QWEN, QWEN_MAN, qwen=True)
    fj = j2a_vals(FLASH); qj = j2a_vals(QWEN)
    fw, fwn = wl_hits(FLASH, FLASH_DIR); qw, qwn = wl_hits(QWEN, QWEN_DIR)
    ft = dict((r[0], r) for r in A.by_template(FLASH))
    qt = dict((r[0], r) for r in A.by_template(QWEN))
    tpls = sorted(set(ft) | set(qt))
    L = []
    def w(s=''):
        L.append(s)
    w('# Qwen vs flash：同 20 题配对（20 题 × 3 抽）\n')
    w('- flash：`_rejudge_flash20261018_v2.txt`（取同 20 题，60 件）；Qwen：`_qwen_shard*.tsvl`（60 件）。')
    w('- 判定口径：`rejudge_existing`，420s / R=10 / 40000；TRUNCATED 取生成侧 manifest，单列。\n')
    w('## 总表\n')
    w('| 指标 | flash 同20题 | Qwen 同20题 |')
    w('|---|---:|---:|')
    w(line('件数', fs['n'], qs['n']))
    w(line('可编译', '%d = %s' % (fs['compilable'], pct(fs['compilable'], fs['n'])),
           '%d = %s' % (qs['compilable'], pct(qs['compilable'], qs['n']))))
    w(line('OK', '%d = %s' % (fs['ok'], pct(fs['ok'], fs['n'])),
           '%d = %s' % (qs['ok'], pct(qs['ok'], qs['n']))))
    for k in ('NO_ENTRY', 'CRASH', 'SYNTAX', 'FIELD_GAP'):
        w(line(k, fs['kinds'].get(k, 0), qs['kinds'].get(k, 0)))
    w(line('TRUNCATED(生成侧)', '%d = %s' % (len(ftr), pct(len(ftr), fs['n'])),
           '%d = %s' % (len(qtr), pct(len(qtr), qs['n']))))
    w(line('字段齐全', '%d = %s' % (fs['complete'], pct(fs['complete'], fs['n'])),
           '%d = %s' % (qs['complete'], pct(qs['complete'], qs['n']))))
    w(line('格级一致', '%d/%d = %s' % (fs['cell_in'], fs['cell_tot'], pct(fs['cell_in'], fs['cell_tot'])),
           '%d/%d = %s' % (qs['cell_in'], qs['cell_tot'], pct(qs['cell_in'], qs['cell_tot']))))
    w(line('件级全一致', '%d/%d = %s' % (fs['item_all'], fs['item_with_cells'], pct(fs['item_all'], fs['item_with_cells'])),
           '%d/%d = %s' % (qs['item_all'], qs['item_with_cells'], pct(qs['item_all'], qs['item_with_cells']))))
    w(line('闭式格级', '%d/%d = %s' % (fc['cell_in'], fc['cell_tot'], pct(fc['cell_in'], fc['cell_tot'])),
           '%d/%d = %s' % (qc['cell_in'], qc['cell_tot'], pct(qc['cell_in'], qc['cell_tot']))))
    w(line('事件驱动格级', '%d/%d = %s' % (fe['cell_in'], fe['cell_tot'], pct(fe['cell_in'], fe['cell_tot'])),
           '%d/%d = %s' % (qe['cell_in'], qe['cell_tot'], pct(qe['cell_in'], qe['cell_tot']))))
    w(line('J2a 可算', len(fj), len(qj)))
    if fj and qj:
        w(line('J2a rel 中位', '%.3g' % sorted(fj)[len(fj)//2], '%.3g' % sorted(qj)[len(qj)//2]))
        w(line('J2a <1e-6 件', sum(1 for v in fj if v < 1e-6), sum(1 for v in qj if v < 1e-6)))
    w(line('W=L/ 代码命中', '%d/%d' % (fw, fwn), '%d/%d' % (qw, qwn)))
    w('')
    w('## 按模板：格级一致（in/tot）\n')
    w('| 模板 | flash | Qwen |')
    w('|---|---:|---:|')
    for t in tpls:
        f = ft.get(t); q = qt.get(t)
        fv = '—' if not f else '%d/%d' % (f[4], f[5])
        qv = '—' if not q else '%d/%d' % (q[4], q[5])
        w('| %s | %s | %s |' % (t, fv, qv))
    w('')
    w('## 读法')
    w('- 同 20 题、同 60 件；**不要**把 Qwen 的 50.5% 和 flash 的 26.9% 全语料直接比。')
    w('- TRUNCATED 是生成侧，不混进判定侧 NO_ENTRY/CRASH；两边单列。')
    w('- `W=L/` 是代码级自证迹象，不是语义错；J2a <1e-6 是同一件事的判据侧旁证。')
    with io.open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    with io.open(OUT_CSV, 'w', encoding='utf-8', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(['metric','flash','qwen'])
        for row in L:
            if row.startswith('| ') and not row.startswith('|---') and '指标' not in row:
                cells = [c.strip() for c in row.strip('|').split('|')]
                if len(cells) == 3:
                    wr.writerow(cells)
    print('OK ->', OUT_MD)
    print('flash:', fs['kinds'], 'cells', fs['cell_in'], '/', fs['cell_tot'], 'trunc', len(ftr))
    print('qwen :', qs['kinds'], 'cells', qs['cell_in'], '/', qs['cell_tot'], 'trunc', len(qtr))


if __name__ == '__main__':
    main()
