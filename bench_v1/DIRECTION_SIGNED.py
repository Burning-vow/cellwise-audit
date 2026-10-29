"""带符号的方向读数：E04(resume 预占) 与 E25(restart) 在三种载体上到底是变好还是变坏。

为什么必须单独跑这一趟：`criteria.rel_dev()`（criteria.py:136）用的是
`abs(est-truth)/abs(truth)` ⇒ 主矩阵里的 rel 列**没有符号**。
而 CATALOG 的 E04 `theory_ref` 主张"差 = E[S]ρ(cv²−1)/(2(1−ρ))：M/D/1 上预占更差、H2 上预占更好"
——这是一个**带方向的断言**，主矩阵根本证不了它。要么实测方向，要么把这句话删掉。

本脚本只做一件事：同一道题跑 REF 与工件，报 (est − truth)/truth 的**带符号**值，W 与 L 各一。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C  # noqa: E402

OUT = io.open(os.path.join(HERE, 'DIRECTION_SIGNED.md'), 'w', encoding='utf-8')
SEEDS, HORIZON = 10, 40000
# 题号一律取自 mutants.jsonl（上一版我猜了 md1-01/mm1-01，那两件根本没有 E04/E25 工件）
PAIRS = [
    ('md1-02', 'REF'), ('md1-02', 'e04'), ('md1-02', 'e25'),
    ('md1-05', 'REF'), ('md1-05', 'e04'), ('md1-05', 'e25'),
    ('mm1-02', 'REF'), ('mm1-02', 'e04'), ('mm1-02', 'e25'),
    ('mmc-03', 'REF'), ('mmc-03', 'e04'), ('mmc-03', 'e25'),
    ('mh2-01', 'REF'), ('mh2-01', 'e04'), ('mh2-01', 'e25'),
    ('mh2-06', 'REF'), ('mh2-06', 'e04'), ('mh2-06', 'e25'),
    # E03/E24 的 CATALOG 句子也主张方向（"W、L 下降"），一并取证；md1 上两者是定义塌缩，不测
    ('mm1-02', 'e03'), ('mm1-02', 'e24'),
    ('mmc-03', 'e03'), ('mmc-03', 'e24'),
    ('mh2-06', 'e03'), ('mh2-06', 'e24'),
]
OBS = ('W', 'L')


def w(s=''):
    # 逐条 flush：上一版后台跑到一半进程没了、缓冲里的 18 段全丢（0 字节文件）。
    # 长链的产物必须边算边落盘，否则"零产出"分不清是慢还是死。
    OUT.write(s + '\n')
    OUT.flush()


def load_tasks():
    d = {}
    for line in io.open(os.path.join(HERE, 'tasks.jsonl'), encoding='utf-8'):
        line = line.strip()
        if line:
            t = json.loads(line)
            d[t['task_id']] = t
    return d


def read_one(path, task):
    obs, wall, note = C.run_artifact(path, SEEDS, HORIZON)
    j1 = C.j1_analytic(obs, task)
    per = j1['per_obs']
    out = {}
    for o in OBS:
        d = per.get(o) or {}
        est, truth = d.get('est'), d.get('truth')
        signed = None
        if est is not None and truth not in (None, 0):
            signed = (est - truth) / abs(truth)
        out[o] = dict(est=est, truth=truth, signed=signed, status=d.get('status'))
    return out, wall, note


def main():
    tasks = load_tasks()
    w('# 带符号方向读数（`DIRECTION_SIGNED.py`，R=%d / horizon=%d）\n' % (SEEDS, HORIZON))
    w('- 主矩阵的 `rel` 列是 `abs()` 后的量（`criteria.py:136`）⇒ **方向不能从主矩阵读**，故本趟单独跑。\n')
    cache = {}
    for tid, tag in PAIRS:
        p = os.path.join(HERE, 'artifacts', '%s__%s.py' % (tid, tag.upper() if tag == 'REF' else tag))
        if not os.path.exists(p):
            w('- **缺文件**：%s（不是 0，是没测过）' % p)
            continue
        try:
            got, wall, note = read_one(p, tasks[tid])
        except Exception as exc:
            w('- %s/%s 跑挂：%s' % (tid, tag, exc))
            continue
        cache[(tid, tag)] = got
        sW, sL = got['W']['signed'], got['L']['signed']
        w('## %s / %s（%.1f s，note=%s）\n' % (tid, tag, wall, (note or '')[:40]))
        w('| 观测量 | est | truth | (est−truth)/truth |')
        w('|---|---|---|---|')
        for o in OBS:
            d = got[o]
            w('| %s | %s | %s | %s |' % (
                o,
                ('%.6f' % d['est']) if d['est'] is not None else '—',
                ('%.6f' % d['truth']) if d['truth'] is not None else '—',
                ('%+.2f%%' % (100 * d['signed'])) if d['signed'] is not None else '—'))
        w('')

    w('## 汇总：工件相对**同题参照件**的方向（这才是"预占更差还是更好"）\n')
    w('| 载体 | 错型 | ΔW vs REF | ΔL vs REF |')
    w('|---|---|---|---|')
    for tid in ('md1-02', 'md1-05', 'mm1-02', 'mmc-03', 'mh2-01', 'mh2-06'):
        ref = cache.get((tid, 'REF'))
        if not ref:
            continue
        for tag in ('e03', 'e04', 'e24', 'e25'):
            got = cache.get((tid, tag))
            if not got:
                continue
            cells = []
            for o in OBS:
                a, b = got[o]['signed'], ref[o]['signed']
                cells.append('%s' % ('%+.2f%%（相对 REF %+.2f%%）' % (100 * a, 100 * b))
                             if (a is not None and b is not None) else '—')
            w('| %s | %s | %s | %s |' % (tid.split('-')[0], tag.upper(), cells[0], cells[1]))
    w('')
    w('## 判读规则（先钉死再读数，不许事后挑方向）\n')
    w('- 若 E04 在 **md1** 上 ΔW>0 而 **H2** 上 ΔW<0 ⇒ CATALOG 那句"符号由 cv²−1 定"至少在本语料两例上同向，保留；')
    w('- 若两例同号 ⇒ **该公式被否证**，`theory_ref` 必须降级成"方向实测如下"，删掉闭式差值公式；')
    w('- 若某载体 ΔW 落在 REF 自身的噪声量级内 ⇒ 只许写"方向不可定"。\n')
    OUT.close()
    print('OK pairs=%d' % len(cache))


if __name__ == '__main__':
    main()
