# -*- coding: utf-8 -*-
"""在 **full64（190 件 weak / 1,348 件）** 上重算 π_K，而不是 346 件那套 mutants.jsonl。"""
import csv
import io
import json
import math
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = io.open(os.path.join(HERE, 'PIK_FULL64.md'), 'w', encoding='utf-8')


def w(s=''):
    OUT.write(s + '\n')


def erlang_loss(lam, mu, c, K):
    a = lam / mu
    s = 1.0 + sum(a ** n / math.factorial(n) for n in range(1, min(c, K) + 1))
    s += sum(a ** n / (math.factorial(c) * c ** (n - c)) for n in range(c + 1, K + 1))
    p0 = 1.0 / s
    return p0 * a ** K / (math.factorial(c) * c ** max(0, K - c))


tasks = {}
for line in io.open(os.path.join(HERE, 'tasks.jsonl'), encoding='utf-8'):
    if line.strip():
        t = json.loads(line)
        tasks[t['task_id']] = t

rows = list(csv.DictReader(io.open(os.path.join(HERE, 'exp_2026-10-19/full64/MUTANT_TAGS_full64.csv'),
                                   encoding='utf-8')))
weak = [r for r in rows if r['expected_declared'] == 'weak']
pairs = sorted({(r['task_id'], r['error_type']) for r in weak})
tag = {(r['task_id'], r['error_type']): r['tag_strict_A'] for r in weak}


def params(t):
    p = t.get('params') or {}
    lam = p.get('lambda') or p.get('lam') or p.get('arrival_rate')
    mu = p.get('mu') or p.get('service_rate')
    c = p.get('c') or p.get('servers') or 1
    K = p.get('K') or p.get('cap') or p.get('capacity')
    return lam, mu, c, K


def collect(mode):
    ok, na = [], []
    for (tid, et) in pairs:
        t = tasks.get(tid)
        lam, mu, c, K = params(t or {})
        if None in (lam, mu, K) or not K:
            na.append((tid, et, 'no capacity in task params'))
            continue
        Ke = K
        if mode == 'class':
            if et == 'E15':
                Ke = K - 3
            elif et == 'E16':
                Ke = K + c
        if Ke < 1:
            na.append((tid, et, 'K_eff<1'))
            continue
        ok.append((tid, et, erlang_loss(lam, mu, c, Ke), lam, mu, c, K, Ke, tag[(tid, et)]))
    return ok, na


w('# full64 上的 π_K（190 件 weak / 1,348 件）\n')
w('- 输入：`exp_2026-10-19/full64/MUTANT_TAGS_full64.csv` 中 `expected_declared=weak` 的行；')
w('- 单位：**(task, class) 对**（每个对恰好 1 件工件，本语料里两者一一对应）。')
w('')
for mode, name in (('task', '题目 K'), ('class', '错型语义 K')):
    ok, na = collect(mode)
    judged = [r for r in ok if r[8] != 'INJECTION_IDLE']
    v = sorted(r[2] for r in judged)
    w('## %s口径\n' % name)
    w('- 可算 **%d** 对（NA %d）；其中判定过（非 IDLE）**%d** 对，涉及 **%d** 题、**%d** 个错型' % (
        len(ok), len(na), len(judged), len({r[0] for r in judged}), len({r[1] for r in judged})))
    if judged:
        w('- π_K 范围 **%.4f–%.4f**，中位 **%.4f**，<1%% 的 **%d** 对，<5%% 的 **%d** 对' % (
            v[0], v[-1], st.median(v),
            sum(1 for x in v if x < 0.01), sum(1 for x in v if x < 0.05)))
        per_task = {}
        for r in judged:
            per_task.setdefault(r[0], []).append(r[2])
        tv = sorted(st.median(x) for x in per_task.values())
        w('- 题级中位数（先题内取中位再跨题）：范围 %.4f–%.4f，中位 **%.4f**；%d 题中低于 1%% 的 %d 题' % (
            tv[0], tv[-1], st.median(tv), len(tv), sum(1 for x in tv if x < 0.01)))
    w('')
    if na:
        w('- NA 明细：%s' % '; '.join('%s/%s（%s）' % (a, b, c) for a, b, c in na[:12]))
        w('')

OUT.close()
print(open(os.path.join(HERE, 'PIK_FULL64.md'), encoding='utf-8').read())
