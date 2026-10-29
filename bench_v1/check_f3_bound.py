"""F3'b 的**上界**到底该写成什么：把 m 与"跨窗口左边界那个忙期"的几何量一起算出来。

为什么要有它：`F3_M_DISTRIBUTION.md` 里我给出了 `m ≤ 该忙期人数`，但那个文件只算了 m，
**忙期人数一个都没算**——等于把一条没验过的界钉进预注册。外部审计（F-2）报 seed 54
m=21 而忙期人数=17，即我这条界被自己的数据否证。这里把三条候选界一起判：
  B1  m ≤ 1                    （§12 的旧界，已知错）
  B2  m ≤ sz                   （我在 §19 / F3_M_DISTRIBUTION.md 钉的那条）
  B3  m ≤ e·j ≤ sz²/4          （e=窗口外人数、j=窗口内人数，逆序对的上界）

口径与 `k0_fast.py` 完全一致：M/D/1 λ=6 μ=10 H=40000 WARM=0.25，`W` 的分母是
**该 seed 里到达时刻 ≥ win_start 的顾客数**（不是 λ·0.75H 的近似值！n 用错了 m 就不是整数）。
忙期由 (arrivals, dur) 直接算：定长服务下工作量过程与取队方式无关 ⇒ 忙期是**路径公共**的，
所以一条 FCFS 流就够；这同时也是"|dW| 只可能来自跨边界那一个忙期"这句机制话的依据。

自校验：重建的流必须先让 fcfs 的 W 与 `K0_rows_md1.csv` **逐位相同**，否则一切作废。
只读，不写任何交付物（只新增本报告）。
"""
import collections
import csv
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import k0_fast as K                                          # noqa: E402

ROWS = os.path.join(HERE, 'K0_rows_md1.csv')
OUT = os.path.join(HERE, 'F3_BOUND_CHECK.md')
LAM, MU, HOR, WARM = 6.0, 10.0, 40000.0, 0.25
WIN0 = WARM * HOR


def busy_periods_real(arrivals, dur):
    """忙期 = 服务器连续忙的极大区间，按顾客下标闭区间给出。

    推进式必须是 `busy_end = busy_end + dur[j]`（排队时新顾客排在**队尾**，服务在既有剩余工作量
    之后才开始），不能写成 `max(busy_end, arrivals[j]+dur[j])`——后者把同时到达的 3 个人算成
    忙期只长 1/μ，会系统性把 sz 算小（我第一版就栽在这里，sz=9 而真值 17）。
    """
    out = []
    i = 0
    n = len(arrivals)
    while i < n:
        busy_end = arrivals[i] + dur[i]
        j = i
        while j + 1 < n and arrivals[j + 1] < busy_end:
            j += 1
            busy_end += dur[j]
        out.append((i, j, arrivals[i], busy_end))
        i = j + 1
    return out


def main():
    want = {}
    for r in csv.DictReader(io.open(ROWS, encoding='utf-8')):
        want[(int(r['seed']), r['disc'])] = r['W']
    seeds = sorted({s for s, _ in want})
    nbad_stream = 0
    rows = []
    for s in seeds:
        arrivals, dur = K.make_stream(s, LAM, MU, True)
        # ---- 自校验：fcfs 的 W 必须逐位相同（只校验前 3 个 seed，全跑太慢）----
        if s <= 3:
            W, _L = K.run_one(arrivals, dur, 'fcfs', s)
            if '%.10f' % W != want[(s, 'fcfs')]:
                nbad_stream += 1
        n_in = sum(1 for a in arrivals if a >= WIN0)        # 该 seed 的真实分母
        bps = busy_periods_real(arrivals, dur)
        # 跨界忙期 = 时间区间 [start, end) 覆盖 win_start 的那个忙期；
        # 窗口左边落在空闲期时**没有**跨界忙期，此时 W 与策略无关，m 必为 0。
        sz = e = j = 0
        str_ = [bp for bp in bps if bp[2] <= WIN0 < bp[3]]
        assert len(str_) <= 1, 'seed %d 覆盖边界的忙期有 %d 个，忙期划分不互斥' % (s, len(str_))
        if str_:
            a0, a1 = str_[0][0], str_[0][1]
            sz = a1 - a0 + 1
            e = sum(1 for k in range(a0, a1 + 1) if arrivals[k] < WIN0)
            j = sz - e
        row = dict(seed=s, n_in=n_in, sz=sz, e=e, j=j)
        for rule in ('lcfs', 'siro'):
            dW = abs(float(want[(s, rule)]) - float(want[(s, 'fcfs')]))
            row[rule] = dW * n_in * MU
        rows.append(row)

    def summar(rule):
        nz = [r for r in rows if r[rule] > 1e-9]
        v1 = [r for r in nz if r[rule] > 1.02]
        v2 = [r for r in nz if r[rule] > r['sz'] + 1e-6]
        v3 = [r for r in nz if r[rule] > r['e'] * r['j'] + 1e-6]
        ints = sorted({int(round(r[rule])) for r in nz})
        worst = max(nz, key=lambda r: r[rule]) if nz else None
        return dict(pairs=len(rows), nz=len(nz), v1=len(v1), v2=len(v2), v3=len(v3),
                    vals=ints, worst=worst)

    lines = ['# F3 余项上界复核（M/D/1 λ=%g μ=%g H=%g 预热 %g，%d 个种子）' % (LAM, MU, HOR, WARM, len(rows)), '']
    lines.append('分母 n 用**该 seed 到达时刻 ≥ %.0f 的顾客数**（不是 λ·0.75H=%.0f 的近似）；'
                 '流重建自校验：fcfs 的 W 与 `K0_rows_md1.csv` 逐位相同的前 3 个 seed 不符数 = **%d**。'
                 % (WIN0, LAM * (HOR - WIN0), nbad_stream))
    if nbad_stream:
        lines += ['', '**流对不上，下面全部作废。**', '']
    lines += ['', '忙期按 (arrivals, dur) 直接划分（定长服务下工作量过程与取队方式无关 ⇒ 忙期是路径公共的）。'
              '`sz`=跨左边界那个忙期的总人数，`e`=其中到达在窗口外的，`j`=窗口内的。', '']
    lines += ['| 规则 | 配对 | m≠0 | B1 `m≤1` 违例 | B2 `m≤sz` 违例 | B3 `m≤e·j` 违例 | m 取值 | 最大 m（seed, sz, e, j） |',
              '|---|---|---|---|---|---|---|---|']
    for rule in ('lcfs', 'siro'):
        st = summar(rule)
        w = st['worst']
        lines.append('| %s | %d | %d | %d | %d | %d | %s | %.0f（seed %d, sz=%d, e=%d, j=%d） |' % (
            rule, st['pairs'], st['nz'], st['v1'], st['v2'], st['v3'],
            ','.join(str(v) for v in st['vals']),
            w[rule], w['seed'], w['sz'], w['e'], w['j']))
    no_bp = sum(1 for r in rows if r['sz'] == 0)
    e1 = collections.Counter(r['e'] for r in rows if r['sz'] > 0)
    # m=0 到底有几类？外部审计第三轮说我只列两类、漏了第三类（33 个）。这里穷举拆：
    #   ① 窗口左边落在空闲期（没有跨界忙期）；② 有跨界忙期但窗口外只有 1 人（不可抢、无从换序）；
    #   ③ e≥2 却仍 m=0：窗口外那几个人与窗口内的人**从未在同一个决策点共存**
    #      （=另一棵引擎里 `trig_nonhead=0` 的语义）。
    for rule in ('lcfs', 'siro'):
        z = [r for r in rows if r[rule] <= 1e-9]
        c1 = sum(1 for r in z if r['sz'] == 0)
        c2 = sum(1 for r in z if r['sz'] > 0 and r['e'] == 1)
        c3 = sum(1 for r in z if r['sz'] > 0 and r['e'] >= 2)
        lines.append('**`m=0` 穷尽拆分（%s）**：零共 %d 个 = ①窗口落在空闲期 %d ＋ ②窗口外只 1 人 %d '
                     '＋ **③e≥2 却仍为 0：%d**（占零的 %.1f%%）⇒ 两类说法**不穷尽**，第三类才是'
                     '"机制活着但没有可换序的时机"，与触发计数器 `trig_nonhead=0` 同义。' % (
                         rule, len(z), c1, c2, c3, 100.0 * c3 / max(len(z), 1)))
        lines.append('')
    lines += ['', '**m=0 的几何解释**：窗口左边落在空闲期（没有跨界忙期）的种子 %d/%d；'
              '有跨界忙期的 %d 个里，"窗口外那一段"的人数 e 分布 = %s。'
              'e=1 时窗口外只有正在受服务的那个人（不可被抢、也无法与窗口内的人换序）⇒ m 必为 0，'
              '这才是 m=0 的主要来源，不是"机制没触发"。' % (
                  no_bp, len(rows), len(rows) - no_bp, dict(sorted(e1.items()))), '',
              '| seed | 规则 | m | 跨界忙期 sz | 窗口外 e | 窗口内 j | e·j | B2 `m≤sz` | B3 `m≤e·j` |',
              '|---|---|---|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda x: -max(x['lcfs'], x['siro'])):
        for rule in ('lcfs', 'siro'):
            if r[rule] > 1e-9:
                lines.append('| %d | %s | %.0f | %d | %d | %d | %d | %s | %s |' % (
                    r['seed'], rule, r[rule], r['sz'], r['e'], r['j'], r['e'] * r['j'],
                    'ok' if r[rule] <= r['sz'] + 1e-6 else '**违例**',
                    'ok' if r[rule] <= r['e'] * r['j'] + 1e-6 else '**违例**'))
    lines += ['', '**结论**：B1（m≤1）、B2（m≤sz）都要在表里报违例才算复核过；'
              '只有 B3（m≤e·j）报 0 违例时，正文的界才写 `m ≤ e·j ≤ sz²/4`。', '']
    txt = '\n'.join(lines) + '\n'
    io.open(OUT, 'w', encoding='utf-8').write(txt)
    sys.stdout.buffer.write(txt.encode('utf-8'))


if __name__ == '__main__':
    main()
