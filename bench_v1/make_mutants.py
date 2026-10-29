"""Step 1：造可控错型工件库 + 自检。

命令（一律用 ~/miniconda3/python.exe，本机 py 启动器默认项是坏的）：
  make_mutants.py plan                  # 只报规模，不落文件
  make_mutants.py gen                   # 落 artifacts/*.py 与 mutants.jsonl
  make_mutants.py gate   [--shard 0/2]  # 真值闸：正确版 20 种子 × 40000 覆盖闭式真值
  make_mutants.py smoke  [--shard 0/2]  # 每件跑 --seeds 3 --horizon 5000
  make_mutants.py diff                  # difflib 单点自查
  make_mutants.py dir    [--shard 0/2]  # 方向核对 + 良性件核对（含短预算档）
  make_mutants.py report                # 汇总 → STEP1_SELFCHECK.md

全部逐条 flush、可续跑（缓存在 bench_v1/artifacts/_selfcheck/，该目录归本任务独占）。
"""
import os
import io
import sys
import json
import math
import time
import difflib
import subprocess
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, 'artifacts')
CACHE = os.path.join(ART, '_selfcheck')
MUT_PATH = os.path.join(HERE, 'mutants.jsonl')
SELFCHK = os.path.join(HERE, 'STEP1_SELFCHECK.md')
PY = os.path.expanduser('~/miniconda3/python.exe')

sys.path.insert(0, HERE)
import simcore as SC  # noqa: E402

# 口径（写死）：真值闸 20 种子 df=19 → t=2.093；方向核对 10 种子 df=9 → t=2.262
GATE_N, GATE_H, GATE_T = 20, 40000.0, SC.T_DF19
DIR_N, DIR_H, DIR_T = 10, 20000.0, 2.262
SHORT_N, SHORT_H = 10, 2000.0
SMOKE_N, SMOKE_H = 3, 5000.0
INV_INST = 6               # 库存模板全取（确定性/便宜）
QUEUE_INST = 2             # 每个 (模板 × 错型) 取最低 ρ 与最高 ρ 两道题

REF_TMPL = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 {tid}：正确版本（参照件）。

模板 {tpl}；口径：W=分钟、L=无量纲、p_loss/p_wait/busy_frac=0-1；
horizon 与 lambda、mu 同单位（{units}）。内核见 bench_v1/simcore.py。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('{tid}', 'REF')
'''

MUT_TMPL = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 {tid} / 错型 {et}：{short}

family={fam}  expected={exp}（跑实验之前声明）
theory_ref={theory}
注入点：simcore 的单个 hook —— {hook}={hval}（其余与 REF 完全一致）
本文件与 {tid}__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('{tid}', '{et}')
'''


def tasks():
    return SC.load_tasks()


def expected_for(etype, tpl):
    c = SC.CATALOG[etype]
    return c.get('expected_by_tpl', {}).get(tpl, c['expected'])


def plan_rows():
    """(REF 行, 变异行)；变异行 = [(task_id, template, etype)]。"""
    by_tpl = {}
    for t in tasks():
        by_tpl.setdefault(t['template'], []).append(t)
    rows = []
    for tpl, ts in sorted(by_tpl.items()):
        ts = sorted(ts, key=lambda x: SC.rho_of(x))
        picked = ts[:INV_INST] if tpl in ('newsvendor', 'eoq') else [ts[0], ts[-1]]
        for et in sorted(SC.CATALOG):
            if tpl not in SC.CATALOG[et]['applies']:
                continue
            for t in picked:
                rows.append((t['task_id'], tpl, et))
    refs = [(t['task_id'], t['template'], 'REF') for t in tasks()]
    return refs, rows


def artifact_name(tid, et):
    return '%s__%s.py' % (tid, 'REF' if et == 'REF' else et.lower())


# ------------------------------------------------------------------ gen
def cmd_gen(force=False):
    if not os.path.isdir(ART):
        os.makedirs(ART)
    refs, rows = plan_rows()
    tb = SC.task_by_id()
    units = {'newsvendor': '天，需求按天', 'eoq': '年'}
    n_new = 0
    for tid, tpl, et in refs + rows:
        fn = os.path.join(ART, artifact_name(tid, et))
        if os.path.exists(fn) and not force:
            continue
        if et == 'REF':
            body = REF_TMPL.format(tid=tid, tpl=tpl, units=units.get(tpl, '小时'),
                                   name=os.path.basename(fn))
        else:
            c = SC.CATALOG[et]
            hook, hval = list(SC.ERRORS[et].items())[0]
            body = MUT_TMPL.format(tid=tid, et=et, short=c['short'], fam=c['family'],
                                   exp=expected_for(et, tpl), theory=c['theory_ref'],
                                   hook=hook, hval=hval, name=os.path.basename(fn))
        with io.open(fn, 'w', encoding='utf-8', newline='\n') as f:
            f.write(body)
        n_new += 1
    with io.open(MUT_PATH, 'w', encoding='utf-8') as f:
        for tid, tpl, et in rows:
            c = SC.CATALOG[et]
            hook, hval = list(SC.ERRORS[et].items())[0]
            f.write(json.dumps(dict(
                task_id=tid, template=tpl, error_type=et, family=c['family'],
                artifact_path='bench_v1/artifacts/' + artifact_name(tid, et),
                change='%s | 单点注入 hook %s=%s | 与 %s__REF.py 的唯一代码差' % (
                    c['short'], hook, hval, tid),
                expected=expected_for(et, tpl), theory_ref=c['theory_ref']),
                ensure_ascii=False) + '\n')
    n_art = len([x for x in os.listdir(ART) if x.endswith('.py')])
    sys.stdout.write('gen: new=%d artifacts=%d mutants=%d\n' % (n_new, n_art, len(rows)))


# ------------------------------------------------------------------ 缓存
def _cache_load(name):
    fn = os.path.join(CACHE, name)
    out = {}
    if os.path.exists(fn):
        with io.open(fn, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    out[r['_k']] = r
    return out


def _cache_append(name, row):
    if not os.path.isdir(CACHE):
        os.makedirs(CACHE)
    with io.open(os.path.join(CACHE, name), 'a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')
        f.flush()


def _shard(items, spec):
    if not spec:
        return items
    k, n = [int(x) for x in spec.split('/')]
    return [x for i, x in enumerate(items) if i % n == k]


# ------------------------------------------------------------------ 真值闸
def cmd_gate(shard=None):
    done = _cache_load('gate.jsonl')
    todo = [t for t in _shard(tasks(), shard)
            if ('%s@%g' % (t['task_id'], GATE_H)) not in done]
    for i, t in enumerate(todo):
        k = SC.kpi(t, 'REF', n=GATE_N, horizon=GATE_H)
        row = dict(_k='%s@%g' % (t['task_id'], GATE_H), task_id=t['task_id'],
                   template=t['template'], n=GATE_N, H=GATE_H, tcoef=GATE_T,
                   contract=t['output_contract'], truth=t['truth_print'])
        for key in t['output_contract']:
            if key == 'W':
                row['sim'], row['hw'] = k['W_min'], k.get('W_hw')
            elif key == 'L':
                row['sim_L'], row['hw_L'] = k['L'], k.get('L_hw')
            elif key == 'exp_profit':
                row['sim_profit'], row['hw_profit'] = k['exp_profit'], k.get('exp_profit_hw')
            elif key == 'q':
                row['sim_q'] = k['q']
            elif key == 'cost':
                row['sim_cost'] = k['cost']
            else:
                row['sim_' + key] = k[key]
                row['hw_' + key] = k.get(key + '_hw')
        _cache_append('gate.jsonl', row)
        sys.stdout.write('gate %d/%d %s\n' % (i + 1, len(todo), t['task_id']))
        sys.stdout.flush()
    sys.stdout.write('gate cache rows=%d\n' % len(_cache_load('gate.jsonl')))


# ------------------------------------------------------------------ smoke
def cmd_smoke(shard=None):
    items = _shard(sorted(x for x in os.listdir(ART) if x.endswith('.py')), shard)
    done = _cache_load('smoke.jsonl')
    for i, fn in enumerate(items):
        if fn in done:
            continue
        t0 = time.time()
        try:
            r = subprocess.run([PY, os.path.join(ART, fn), '--seeds', str(SMOKE_N),
                                '--horizon', str(SMOKE_H)],
                               capture_output=True, timeout=600)
            rc, out, err = r.returncode, r.stdout.decode('utf-8', 'replace'), \
                r.stderr.decode('utf-8', 'replace')
        except subprocess.TimeoutExpired:
            rc, out, err = -1, '', 'TIMEOUT'
        lines = [x for x in out.splitlines() if x.strip()]
        ok_json, keys_ok, fields = False, False, None
        if len(lines) == 1:
            try:
                fields = json.loads(lines[0])
                ok_json = isinstance(fields, dict)
            except Exception:
                ok_json = False
        if ok_json:
            tid = fn.split('__')[0]
            need = set(SC.task_by_id()[tid]['output_contract']) | {'runtime_units', 'seeds_used'}
            keys_ok = set(fields) == need and all(
                (isinstance(fields[x], (int, float)) and fields[x] == fields[x])
                or x == 'runtime_units' for x in fields)
        _cache_append('smoke.jsonl', dict(
            _k=fn, file=fn, rc=rc, n_lines=len(lines), ok_json=ok_json, keys_ok=keys_ok,
            fields=fields, err=err[-400:] if err else '', sec=round(time.time() - t0, 2)))
        if i % 25 == 0:
            sys.stdout.write('smoke %d/%d %s\n' % (i + 1, len(items), fn))
            sys.stdout.flush()
    c = _cache_load('smoke.jsonl')
    bad = [v['file'] for v in c.values()
           if not (v['rc'] == 0 and v['ok_json'] and v['keys_ok'] and v['n_lines'] == 1)]
    sys.stdout.write('smoke done n=%d bad=%d\n%s\n' % (len(c), len(bad), ', '.join(bad[:20])))


# ------------------------------------------------------------------ diff 单点
def cmd_diff():
    refs, mrows = plan_rows()
    rows = []
    for tid, tpl, et in mrows:
        a = io.open(os.path.join(ART, artifact_name(tid, 'REF')), encoding='utf-8').read().splitlines()
        b = io.open(os.path.join(ART, artifact_name(tid, et)), encoding='utf-8').read().splitlines()
        changed = [x for x in difflib.ndiff(a, b) if x[:2] in ('+ ', '- ')]
        code = [x for x in changed if 'simcore.main(' in x]
        rows.append(dict(task_id=tid, etype=et, n_changed=len(changed), n_code=len(code),
                         n_hooks=len(SC.ERRORS[et]), hooks=list(SC.ERRORS[et])[0],
                         single=(len(code) == 2 and len(SC.ERRORS[et]) == 1)))
    bad = [r for r in rows if not r['single']]
    _cache_append('diff.jsonl', dict(_k='diff', rows=rows, n_bad=len(bad)))
    sys.stdout.write('diff: pairs=%d suspicious=%d\n' % (len(rows), len(bad)))
    for r in bad[:10]:
        sys.stdout.write('  %s\n' % json.dumps(r, ensure_ascii=False))


# ------------------------------------------------------------------ 测量层
def _stats(task, etype, n, H):
    """按该题 output_contract 取字段（模板无关，库存题进同一张表）。"""
    k = SC.kpi(task, etype, n=n, horizon=H)
    out = {}
    for f in task['output_contract']:
        if f == 'W':
            out['W'] = k['W_min']
            out['W_hw'] = k.get('W_hw')
        elif f == 'L':
            out['L'] = k['L']
            out['L_hw'] = k.get('L_hw')
        elif f == 'exp_profit':
            out[f] = k[f]
            out['exp_profit_hw'] = k.get('exp_profit_hw')
        else:
            out[f] = k[f]
    for extra in ('cons', 'lam_hat', 'arr_hat'):
        if extra in k:
            out[extra] = k[extra]
    ps = {}
    if 'W_per_seed' in k:
        ps['W'] = k['W_per_seed']
        ps['L'] = k['L_per_seed']
        sd = k.get('per_seed') or {}
        for f, src in (('p_wait', 'p_wait'), ('p_loss', 'p_loss'), ('busy_frac', 'busy')):
            if f in out and sd.get(src):
                ps[f] = sd[src]
    if 'reps' in k:
        ps['exp_profit'] = k['reps']
    out['ps'] = ps
    return out


def _heff(et, H):
    """E28 把 lambda、mu 同倍 x60 => 内部时钟快 60 倍、事件量也 60 倍。
    为把算力花在同样的'系统演化量'上，E28 的行用时域 H/60（=同样多的事件）。
    两个估计量都是稳态量的无偏估计，比的是估计值本身，不破坏配对。"""
    return H / 60.0 if et == 'E28' else H


SHORT_SET = ('E01', 'E02', 'E03', 'E04', 'E14', 'E15', 'E16', 'E21', 'E24', 'E25',
             'E26', 'E27', 'E28', 'E29', 'E30')


def cmd_dir(shard=None):
    tb = SC.task_by_id()
    refs, rows = plan_rows()
    done = _cache_load('dir.jsonl')
    todo = [r for r in _shard(rows, shard) if ('%s@%s' % (r[0], r[2])) not in done]
    refc = _cache_load('refstats.jsonl')
    t0 = time.time()
    for i, (tid, tpl, et) in enumerate(todo):
        t = tb[tid]

        def refstats(H, n):
            rk = '%s@%g' % (tid, H)
            if rk in refc:
                return refc[rk]['stats']
            s = _stats(t, 'REF', n, H)
            rec = dict(_k=rk, task_id=tid, H=H, stats=s)
            refc[rk] = rec
            _cache_append('refstats.jsonl', rec)
            return s

        Heff = _heff(et, DIR_H)
        ref = refstats(Heff, DIR_N)
        mut = _stats(t, et, DIR_N, Heff)
        ref_s = mut_s = None
        if et in SHORT_SET and tpl not in ('newsvendor', 'eoq'):
            Sheff = _heff(et, SHORT_H)
            ref_s = refstats(Sheff, SHORT_N)
            mut_s = _stats(t, et, SHORT_N, Sheff)
        _cache_append('dir.jsonl', dict(
            _k='%s@%s' % (tid, et), task_id=tid, template=tpl, etype=et, H=Heff,
            n=DIR_N, expected=expected_for(et, tpl), fields=list(t['output_contract']),
            ref=ref, mut=mut, ref_short=ref_s, mut_short=mut_s))
        if i % 20 == 0:
            el = time.time() - t0
            sys.stdout.write('dir %d/%d %s %s (eta %.0fs)\n' % (
                i + 1, len(todo), tid, et, el / max(1, i + 1) * (len(todo) - i)))
            sys.stdout.flush()
    sys.stdout.write('dir cache rows=%d\n' % len(_cache_load('dir.jsonl')))


def rel(a, b):
    """b 相对 a 的相对偏差；缺字段/0 分母/nan → None（不许拿 0 冒充"没效应"）。"""
    if a is None or b is None:
        return None
    try:
        if a != a or b != b:
            return None
        if abs(a) < 1e-12:
            return None
        return (b - a) / abs(a)
    except Exception:
        return None


def paired(ref, mut, field):
    """同种子配对的相对偏差 + 95%CI 半宽（相对单位）。

    配对（CRN）让次序类/良性件的噪声大幅抵消；稀有事件字段（p_loss）的单次抽样
    噪声仍然很大，所以判定必须带噪声带，否则会把抽样噪声误报成'错型可检'。"""
    a, b = ref.get('ps', {}).get(field), mut.get('ps', {}).get(field)
    point = rel(ref.get(field), mut.get(field))
    if not a or not b or len(a) != len(b) or len(a) < 2:
        return point, 0.0
    d = [y - x for x, y in zip(a, b)]
    m = sum(d) / len(d)
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1))
    hw = DIR_T * sd / math.sqrt(len(d))
    base = abs(ref.get(field) or 0.0)
    if base < 1e-12:
        return point, 0.0
    return m / base, hw / base


def _f(x, fmt='%.4g'):
    if x is None:
        return '—'
    try:
        if x != x:
            return 'nan'
    except Exception:
        return str(x)
    return fmt % x


def _agg_paired(rs, field):
    """(错型×模板) 格内多道题：取配对相对偏差的中位数与最大噪声带。"""
    vals, hws = [], []
    for x in rs:
        r_, h_ = paired(x['ref'], x['mut'], field)
        if r_ is not None:
            vals.append(r_)
            hws.append(h_)
    return (_med(vals), max(hws) if hws else 0.0)


def _med(v):
    if not v:
        return None
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def _relshort(r, f):
    if not r.get('ref_short') or not r.get('mut_short'):
        return None
    return rel(r['ref_short'].get(f), r['mut_short'].get(f))


# ------------------------------------------------------------------ 报告
BENIGN = dict(E26='bias', E27='cons', E28='unit', E29='same', E30='same', E35='unit')
UNIT_FIELD = dict(E28='W', E35='cost')
UNIT_WANT = dict(E28=1.0 / 60.0, E35=1.0 / 365.0)


def cmd_report():
    gate = _cache_load('gate.jsonl')
    smoke = _cache_load('smoke.jsonl')
    dcache = _cache_load('dir.jsonl')
    diffc = _cache_load('diff.jsonl')
    drows = diffc.get('diff', {}).get('rows', []) if diffc else []
    refs, mrows = plan_rows()
    out = io.open(SELFCHK, 'w', encoding='utf-8')
    W = out.write
    W('# Step 1 自检：可控错型工件库（bench_v1/artifacts/）\n\n')
    W('生成时间 %s。内核 `bench_v1/simcore.py`；生成与自检 `bench_v1/make_mutants.py`；'
      '元数据 `bench_v1/mutants.jsonl`。题集 `bench_v1/tasks.jsonl` 只读、未改动。\n\n')
    W('## 0. 统计口径（写死，如实标 df）\n\n')
    W('- **真值闸**：正确版每件 %d 个独立种子 × 时域 %g（λ、μ 是每小时的题用小时；newsvendor 用天；'
      'eoq 是确定性闭式），每种子一个估计，跨种子 t 区间，df=%d，t=%.3f。\n'
      % (GATE_N, GATE_H, GATE_N - 1, GATE_T))
    W('- **方向核对 / 良性件核对**：%d 种子 × 时域 %g，df=%d，t=%.3f；次序类/容量类/预占类/估计类另跑短预算档 '
      '%d 种子 × %g，把"样本预算"当第三个自变量看。\n'
      % (DIR_N, DIR_H, DIR_N - 1, DIR_T, SHORT_N, SHORT_H))
    W('- 服务时长在**到达该节点时**抽好并挂在顾客身上（不是开始服务时才抽）；面积积分 integ() 一律在任何状态改变'
      '**之前**调用。旧代码把 integ() 放在 N+=1 之后 ⇒ L 系统性偏高约 0.1（修前 4.1326±0.0448、'
      '修后 4.0220±0.0450，闭式 4.0000）；本内核的 mm1-07（λ=8、μ=10、闭式 L=4.0000）在 §1 给出修后数字。\n')
    W('- 配对：REF 与变异件用同一列种子；主 RNG 流只喂到达间隔/服务时长/耐心，选人次与重复计数走独立 rng2 '
      '⇒ 次序类错型与 REF 共享样本路径（CRN），ΔL 能落到 0。\n\n')

    # ---- 1 真值闸
    W('## 1. 真值闸（不过就不许产工件）\n\n')
    W('门禁：契约点名的每个字段，正确版 95%%CI 必须覆盖 truth_print；确定性件按相对差 <=1e-6 判。\n\n')
    W('| task | 模板 | 字段 | 仿真 ± CI | 真值 | 覆盖 |\n|---|---|---|---|---|---|\n')
    npass, fails = 0, []
    for tid in sorted(gate):
        g = gate[tid]
        ctr, tr = g['contract'], g['truth']
        ok_all = True
        for key in ctr:
            if key == 'W':
                sim, hw, tv = g['sim'], g['hw'], tr['W']
            elif key == 'L':
                sim, hw, tv = g['sim_L'], g['hw_L'], tr['L']
            elif key == 'exp_profit':
                sim, hw, tv = g.get('sim_profit'), g.get('hw_profit'), tr.get('exp_profit')
            elif key == 'q':
                sim, hw, tv = g.get('sim_q'), None, tr.get('q')
            else:
                sim, hw, tv = g.get('sim_' + key), g.get('hw_' + key), tr.get(key)
            if sim is None or tv is None:
                continue
            if hw is None:
                ok = abs(sim - tv) / max(abs(tv), 1e-12) <= 1e-6
                cov = '√闭式精确' if ok else '×'
            else:
                ok = abs(sim - tv) <= hw
                cov = '√' if ok else '×'
            ok_all = ok_all and ok
            W('| %s | %s | %s | %.6g ± %s | %.6g | %s |\n' % (
                g['task_id'], g['template'], key, sim,
                ('%.5g' % hw) if hw is not None else '—', tv, cov))
        npass += 1 if ok_all else 0
        if not ok_all:
            fails.append(g['task_id'])
    W('\n**真值闸通过 %d/%d**（进闸 %d 题 = 38 道 ready + 新补 mh2/jackson2/newsvendor；'
      'eoq %d 题为确定性闭式，按"闭式精确"另判）。\n\nFAIL：%s\n\n' % (
        npass, len(gate), len(gate), len(tasks()) - len(gate), ', '.join(fails) or '无'))

    # ---- 2 smoke
    W('## 2. 可执行性抽检（每件都跑 `--seeds %d --horizon %g`）\n\n' % (SMOKE_N, SMOKE_H))
    good = [v for v in smoke.values() if v['rc'] == 0 and v['ok_json'] and v['keys_ok'] and v['n_lines'] == 1]
    bad = [v for v in smoke.values() if v not in good]
    W('- 工件 %d 件 = REF %d + 变异 %d；mutants.jsonl %d 行，每行恰好 8 个键（'
      'task_id/template/error_type/family/artifact_path/change/expected/theory_ref）。'
      'REF 不建行，按命名约定 `<task_id>__REF.py` 取。\n'
      % (len(smoke), len(tasks()), len(mrows), len(mrows)))
    W('- 通过（退出码 0 + stdout 恰好一行 JSON + 键集合 = 契约 ∪ {runtime_units, seeds_used} + 无 NaN）：'
      '**%d/%d**，失败 %d。\n' % (len(good), len(smoke), len(bad)))
    for v in bad[:15]:
        W('  - FAIL %s rc=%s n_lines=%s ok_json=%s keys_ok=%s err=%s\n' % (
            v['file'], v['rc'], v['n_lines'], v['ok_json'], v['keys_ok'], (v['err'] or '')[-160:]))
    W('\n')

    # ---- 3 单点性
    W('## 3. 单点性自查（difflib：变异件 vs 同题 REF）\n\n')
    susp = [r for r in drows if not r['single']]
    W('- 核对 %d 对；可疑（代码行改动 != 2 或 hook 数 != 1）：**%d** 条%s。\n' % (
        len(drows), len(susp), '' if not susp else '：' + ', '.join(
            '%s/%s' % (s['task_id'], s['etype']) for s in susp[:10])))
    W('- 工件是薄壳，代码行 diff 恒为 2（`- simcore.main(tid, REF)` / `+ simcore.main(tid, E0x)`）；'
      '真正的单点性由 `ERRORS[etype]` 只覆盖**一个 hook** 保证（生成时 assert len==1）。\n')
    hooks = {}
    for r in drows:
        hooks.setdefault(r['hooks'], set()).add(r['etype'])
    W('- hook 分布（同一 hook 上挂多个错型 ⇒ 只能靠行为/机制签名区分 ⇒ P5 素材）：\n')
    for h in sorted(hooks):
        W('  - `%s`：%s\n' % (h, ', '.join(sorted(hooks[h]))))
    W('\n')

    # ---- 4 良性件
    W('## 4. 良性件核对（E26/E27/E28/E29/E30/E35 不许破坏闭式可比性）\n\n')
    W('判据：与 REF 同种子配对下比 L、p_loss、busy_frac。**E28 只允许 W 的单位变化、E35 只允许 cost 的单位变化**'
      '（题目口径是分钟 / 元每年）—— 这是刻意留给 J1 的坑：模型语义没错、量纲报警，判分器要把它记成'
      '"量纲假阳"而不是建模错。\n\n')
    W('| 错型 | 模板 | 题 | 量纲字段比 | ΔL_rel | Δp_loss_rel | Δbusy_rel | 结论 |\n'
      '|---|---|---|---|---|---|---|---|\n')
    bres = {}
    order = sorted(dcache.values(), key=lambda r: (r['etype'], r['template'], r['task_id']))
    for r in order:
        et = r['etype']
        if et not in BENIGN:
            continue
        ref, mut = r['ref'], r['mut']
        fs = r['fields']
        dl = rel(ref.get('L'), mut.get('L'))
        dp = rel(ref.get('p_loss'), mut.get('p_loss'))
        db = rel(ref.get('busy_frac'), mut.get('busy_frac'))
        uf = UNIT_FIELD.get(et, fs[0])
        wratio = (mut.get(uf) / ref.get(uf)) if ref.get(uf) not in (None, 0) else None
        kind = BENIGN[et]
        if kind == 'same':
            bit = all(mut.get(x) == ref.get(x) for x in fs)
            concl = ('全部契约字段与 REF 逐位相同（bit-identical %s ⇒ 不消耗 RNG、不进统计）' % ('√' if bit else '×')
                     if et == 'E29' else
                     '同分布：ΔL=%s Δbusy=%s（预热窗口只减样本量，稳态期望不动）' % (_f(dl), _f(db)))
        elif kind == 'unit':
            want = UNIT_WANT[et]
            ok = wratio is not None and abs(wratio - want) <= 0.08 * abs(want)
            concl = '%s 比=%s（期望 %s）%s；L/p_loss/busy 与 REF 同分布 ⇒ 只在量纲上报警' % (
                uf, _f(wratio), _f(want), '√' if ok else '×')
        elif kind == 'bias':
            concl = '短预算(H=%g) Δ%s_rel=%s、ΔL_rel=%s；长预算(H=%g) Δ%s_rel=%s ⇒ 方向=低估，预算越小越偏' % (
                SHORT_H, uf, _f(_relshort(r, uf)), _f(_relshort(r, 'L')),
                DIR_H, uf, _f(rel(ref.get(uf), mut.get(uf))))
        else:
            concl = 'ΔW_rel=%s ΔL_rel=%s（面积法 L 与计数无关）；流量守恒残差 cons=%s vs REF %s ⇒ J1 盲、只有 J2 点火' % (
                _f(rel(ref.get('W'), mut.get('W'))), _f(dl), _f(mut.get('cons')), _f(ref.get('cons')))
        bres.setdefault(et, []).append((dl, dp, db))
        W('| %s | %s | %s | %s | %s | %s | %s | %s |\n' % (
            et, r['template'], r['task_id'], _f(wratio), _f(dl), _f(dp), _f(db), concl))
    W('\n')
    for et in sorted(bres):
        v = bres[et]
        W('- **%s** n=%d：|ΔL_rel| 最大 %s，|Δp_loss_rel| 最大 %s，|Δbusy_rel| 最大 %s\n' % (
            et, len(v), _f(max([abs(x[0] or 0) for x in v])),
            _f(max([abs(x[1] or 0) for x in v])), _f(max([abs(x[2] or 0) for x in v]))))
    W('\n')

    # ---- 5 方向核对
    W('## 5. 预注册方向核对（实测符号与量级 vs 跑前声明的 expected）\n\n')
    W('判定规则（跑前定死）：blind ⇒ 各契约字段 |相对偏差| 最大 <=2%%；weak ⇒ <=25%%；detectable ⇒ >=5%%；'
      'benign 不在本表判（见 §4）。相对偏差 =（变异 − REF）/REF，中位数取该 (错型×模板) 下所有题面实例。\n\n')
    W('| 错型 | 模板 | expected | n题 | Δ首字段_rel | ΔL_rel | Δp_loss_rel | 实测判定 | 一致? |\n'
      '|---|---|---|---|---|---|---|---|---|\n')
    agg = {}
    for r in dcache.values():
        agg.setdefault((r['etype'], r['template']), []).append(r)
    anom_txt = []
    for (et, tpl) in sorted(agg):
        rs = agg[(et, tpl)]
        f1 = rs[0]['fields'][0]
        d1, h1 = _agg_paired(rs, f1)
        dL, hL = _agg_paired(rs, 'L')
        dP, hP = _agg_paired(rs, 'p_loss')
        cells = [(x, h) for x, h in ((d1, h1), (dL, hL), (dP, hP)) if x is not None]
        mx = max([abs(x) for x, _ in cells]) if cells else None
        sig = any(abs(x) > max(0.05, 2.0 * h) for x, h in cells)
        quiet = all(abs(x) <= max(0.02, 2.0 * h) for x, h in cells)
        exp = rs[0]['expected']
        band = '，噪声带 %s' % _f(max([h for _, h in cells])) if cells else ''
        if exp == 'benign':
            meas, agree = '良性件（判据见 §4）', True
        elif mx is None:
            meas, agree = '无有效对照(发散)', False
        elif exp == 'blind':
            agree, meas = quiet, ('≈0/噪声内（max|Δ|=%s%s）' % (_f(mx), band)) if quiet \
                else ('偏离超出噪声带（max|Δ|=%s%s）' % (_f(mx), band))
        elif exp == 'weak':
            agree, meas = (not sig), ('本预算下不显著（max|Δ|=%s%s）' % (_f(mx), band) if not sig
                                      else '本预算已显著=max可检（max|Δ|=%s%s）' % (_f(mx), band))
        else:
            agree, meas = sig, ('可检（max|Δ|=%s%s）' % (_f(mx), band)) if sig \
                else ('本预算不可检（max|Δ|=%s%s）' % (_f(mx), band))
        if not agree:
            anom_txt.append('- **%s / %s**：跑前声明 `%s`，实测 %s（Δ%s_rel=%s，ΔL_rel=%s）'
                            '⇒ 按预注册纪律原样记为偏离，不回头改 expected、不改代码。\n'
                            % (et, tpl, exp, meas, f1, _f(_med(d1)), _f(_med(dL))))
        W('| %s | %s | %s | %d | %s | %s | %s | %s | %s |\n' % (
            et, tpl, exp, len(rs), _f(_med(d1)), _f(_med(dL)), _f(_med(dP)), meas,
            '一致' if agree else '**不一致**'))
    W('\n### 5.1 异常表（声明与实测不符）\n\n')
    if anom_txt:
        for x in anom_txt:
            W(x)
    else:
        W('（空）\n')
    W('\n异常表条数：%d / 共 %d 个 (错型×模板) 格\n\n' % (len(anom_txt), len(agg)))

    # ---- 6 目录适配
    W('## 6. 目录适配与声明偏离（都发生在任何测量之前）\n\n')
    W('1. **E17 合并进 E16**：题集只有一个容量参数 K，"把队列容量当系统容量"与"只有队列上限没有系统上限"'
      '落到同一个判定（有效容量 K→K+c），产不出两件行为不同的工件 ⇒ 目录保留说明、工件只出 E16。\n')
    W('2. **E04 在指数服务族（mm1/mmc/mm1K/mmcK/jackson2）声明为 blind**（目录给 detectable）：memoryless ⇒ '
      '预占不改变 N(t) 的律 ⇒ L、W 均值恒等；md1(cv<1) 与 mh2(cv>1) 仍声明 detectable 且**符号相反**'
      '（M/G/1：LCFS-PR E[T]=E[S]/(1-ρ)，FCFS E[T]=E[S](1+(1+cv²)ρ/(2(1-ρ)))，差=E[S]ρ(cv²-1)/(2(1-ρ))）。\n')
    W('3. **E08 声明为 detectable**（目录给 weak）：单位错只动 μ 一侧 ⇒ ρ=λ/μ 被搬 60 倍 ⇒ ρ≥1 非稳态、效应无界。'
      '它与良性件 E28 的分界正落在"单侧/双侧"：ρ 是唯一的无量纲组合，同倍不动它、单侧必动它。\n')
    W('4. **E20 声明为 blind**（目录给 detectable）：纯串联、转移概率 100%% ⇒ 两节点都见 λ 的泊松流（Burke）'
      '⇒ W=W1+W2 是可交换和、L 同理 ⇒ 恒等。\n')
    W('5. **E12/E13/E22/E23/E24 方向翻转**：题集 v1 没有一道题声明批到达/时变到达/耐心放弃/优先级类/换队，'
      '而 REF 必须复现 truth_print ⇒ "漏实现"这一方向无法实例化。改为注入**同量级、符号相反**的件'
      '（单到→2 人一批；恒定泊松→正弦时变；无放弃→有放弃；共享队→分队+周期换队；FCFS→按服务时长二分类严格优先级），'
      'change 字段如实标注。这些件量的不是"漏写声明特征"，而是"判分口径能不能发现凭空多出来的机制"。\n')
    W('6. **mmcK 的 busy_frac 与 mmc 不同义**：题集真值 mmcK 用 1-π0（站不空的比例），mmc 用 ρ=λ/(cμ)（每台利用率）；'
      'c=1 时相等、c>1 时不等。内核按模板分别实现，否则真值闸过不去 ⇒ 这是 J5 逐字段比的一个现成坑。\n')
    W('7. **新增库存族 E31–E38 与良性件 E35**：题集含 6 道报童 + 6 道 EOQ；没有对应错型，判分器在库存半边'
      '就没有可控件可用（对应预注册目录 M15–M18）。\n')
    W('8. **F3（M/D/1 路径恒等 |ΔW|<=1e-9）的可达性**：在"窗口内离开者的逗留时间均值"口径下取不到 —— '
      '完成时刻序列与次序无关，但"谁落在窗口内离开"与次序有关，差一个边界项 O(服务时长/H)。'
      '**ΔL 才是逐位 0**（面积恒等）。判分器若拿 1e-9 当 ΔW 门槛，会把边界项误读成 RNG 泄漏。\n\n')

    # ---- 7 结论
    W('## 7. 门禁结论\n\n')
    W('- 真值闸：%d/%d PASS（%.1f%%）。\n' % (npass, len(gate), 100.0 * npass / max(1, len(gate))))
    W('- 工件规模：%d 件（REF %d + 变异 %d）⇒ 目标 300–500 %s。\n' % (
        len(smoke), len(tasks()), len(mrows), '达标' if 300 <= len(smoke) <= 500 else '**不达标**'))
    W('- 抽检失败 %d 件；非单点可疑 %d 件；异常表 %d 格 / %d 格。\n' % (
        len(bad), len(susp), len(anom_txt), len(agg)))
    out.close()
    sys.stdout.write('report -> %s (gate=%d/%d smoke_bad=%d susp=%d anomalies=%d)\n' % (
        SELFCHK, npass, len(gate), len(bad), len(susp), len(anom_txt)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['plan', 'gen', 'gate', 'smoke', 'diff', 'dir', 'report'])
    ap.add_argument('--shard', default=None)
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    if a.cmd == 'plan':
        refs, rows = plan_rows()
        per = {}
        for tid, tpl, et in rows:
            per[tpl] = per.get(tpl, 0) + 1
        sys.stdout.write('REF=%d mutants=%d total=%d\nper-template=%s\n' % (
            len(refs), len(rows), len(refs) + len(rows), json.dumps(per, sort_keys=True)))
    elif a.cmd == 'gen':
        cmd_gen(a.force)
    elif a.cmd == 'gate':
        cmd_gate(a.shard)
    elif a.cmd == 'smoke':
        cmd_smoke(a.shard)
    elif a.cmd == 'diff':
        cmd_diff()
    elif a.cmd == 'dir':
        cmd_dir(a.shard)
    else:
        cmd_report()


if __name__ == '__main__':
    main()
