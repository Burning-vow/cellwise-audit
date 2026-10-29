"""主矩阵汇总 v2：**逐格 τ\\*、且判定预算与 τ\\* 标定预算必须相同**。

为什么要换掉 summarize_corrected.py：
  1) 它用全局 `TAU='0.02'` —— 与本文主张（τ\\* 是逐格、随预算变的）**自相矛盾**；
  2) 它读的矩阵是 `MM_SEEDS=50` 测的，而 τ\\* 在 10 种子口径上标定 ⇒ 跨预算比阈值。
本脚本把这两条一起关掉：τ\\* 从 `table_tau_v2.csv` 按 (template, criterion, statistic) 查，
判定的 `rel` 来自指定预算的矩阵；查不到 τ\\* 的组合**显式计数并报出来**，绝不给默认值
（默认值就是"静默把未标定当已标定"，这个项目为此付过学费）。

同时报三套口径，方便看出规则差异的影响，也防止分母被混用：
  A 逐格 τ\\*（本文主张的判法）
  B 全局 0.02（旧版做法，只作对照）
  C 检出是否只靠"运行期崩"（崩不等于数值可检）

用法：~/miniconda3/python.exe summarize_matrix_v2.py [MUTANT_MATRIX_R10.csv]
"""
import csv
import io
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
MUT = os.path.join(HERE, 'mutants.jsonl')
TAUT = os.path.join(HERE, 'table_tau_v2.csv')
BEN = os.path.join(HERE, 'BENIGN_PROOF.csv')
# 没有 RELABEL 字典 —— 这里曾经有一份 {'E28','E35'}，那两条错型现在的下场**不一样**（10-18 回出处核）：
#   E28 = 发射器改成"输入/输出口径一起换" ⇒ 真良性，`BENIGN_PROOF.csv` 里 14 件全 PROVES_BENIGN；
#   E35 = 只换输入侧、cost 的口径没跟着换 ⇒ 量纲错，10-17 改判 detectable（J1inv|cost rel≈0.997），
#         不在 BENIGN_PROOF 里。所以任何"把 E28/E35 一起当良性标本"的句子都是过期结论。
# ⚠ 这里原来还写死了"14 件 / 188 变 202 / 98.9% 掉成 92.1%"和"mutants.jsonl 标 benign 74"：
#   两组数与现行表都不对应（benign 现算 = 68）⇒ 注释里不许留字面量，要引用就现算（审计 P-20）。
# 标签唯一来源是 mutants.jsonl；良性件另外与自证闸交叉核对（见 main 末尾）。
# 标签唯一来源是 mutants.jsonl；良性件另外与自证闸交叉核对（见 main 末尾）。
STAGE2CRIT = {'J1': 'J1', 'J1inv': 'J1', 'J2': 'J2', 'J3': 'J3'}
TAGS = ('TP', 'MISS', 'NA_NOINST', 'NA_NOTAU', 'BLIND_CONFIRM', 'BLIND_BUT_FIRED', 'FP', 'BENIGN_OK',
        'BENIGN_UNPROVEN', 'WEAK_FIRED', 'WEAK_QUIET', 'UNKNOWN', 'INJECTION_IDLE')

# ---- 注入是否真落地（P-02/P-03）：恒等类与漏检的**身份**要由机制计数器判，不由"数与参照件相同"猜 ----
# 每个错型只看它自己那条机制；计数器全 0 ⇒ 这件没触发 ⇒ INJECTION_IDLE：
# 既不算"判据看不见"（盲区证实），也不算"漏检"，不进任何分母，但必须逐条点名。
# 反例就在眼前：`md1-02/E01` 的非队首选取发生了 111538 次而读数逐位不变 ⇒ 那是 M/D/1
# 路径恒等（引理 C）**真跑起来**的样子，是恒等类里最强的证据，绝不能被当成空转剔掉。
IDLE_GATE = {
    'E01': ('trig_nonhead',),                    # LCFS：取过非队首才算改了规则
    'E02': ('trig_nonhead',),                    # SIRO：同上
    'E03': ('trig_nonhead',),                    # SPT：定长服务下恒取队首 ⇒ 0
    'E24': ('trig_nonhead',),                    # 优先级类：分类算了但选取没变过 ⇒ 与 FCFS 无异
    'E04': ('trig_preempt', 'trig_nonhead'),     # 预占：两条任一发生即算落地
    'E25': ('trig_preempt', 'trig_nonhead'),
    'E20': ('trig_transfer',),                   # 工序换序：得有转派可换（另有静态 swap_noop）
    # ---- 2026-10-18 由腿 B 真实错型反向补的 5 类，各自的机制计数器 ----
    # E39/E40/E43 是**静态出口覆盖**，计数器数的是"被覆盖的种子序列条数"，不是运行期事件；
    # 这一区别要在报告里说清楚：它们的"≥1"只证明算子走了这一支，不证明有随机路径参与。
    'E39': ('trig_fieldconst',),
    'E40': ('trig_fieldconst',),
    'E41': ('trig_leak',),                       # 真事件计数：一个槽位都没被吃掉就是没落地
    'E42': ('trig_lostcycle',),                  # 被 floor() 丢掉的周期残量，题集里 4/6 题精确为 0
    'E43': ('trig_backsolve',),
}


def emit(s=''):
    """字节安全地往 stdout 写：控制台是 cp936 时 print('⇒') 会先崩在编码上，
    症状是 rc=1、'报告没生成'（其实文件已写好）——把工具自己的编码问题伪装成交付物失败。"""
    sys.stdout.buffer.write((str(s) + chr(10)).encode('utf-8', 'replace'))


def wilson_upper0(n, z=1.96):
    den = 1.0 + z * z / n
    return ((z * z / (2.0 * n)) + z * ((z * z / (4.0 * n * n)) ** 0.5)) / den


def load_tau():
    """返回 (τ\\* 字典, 空判据格集合)。

    第二项是 10-18 补的：`build_tables_v2.py` 会把"参照件上恒为 0、且理由是**定义**而不是测量"的格
    标成 `R0_VACUOUS_INTERNAL`（现在只有 `J2c_busy = max(0, busy_frac−1)`，而 `busy_util≤1`、
    `1−π0≤1` 由定义成立 ⇒ 这条对我方所有工件永不点火）。10-17 那轮我只做到"**能标记**"，
    汇总器根本不按 `rule` 过滤 ⇒ 标记等于没做（第四轮 R4 的后半句抓的就是这个）。
    现在这些格照样算交叉核对（它们确实在验 rel=0），但**不进"独立判据"的计数**，并现算报出条数。
    """
    t, vac = {}, set()
    for r in csv.DictReader(io.open(TAUT, encoding='utf-8')):
        if r['tau_star'] in ('', 'NONE'):
            continue
        k = (r['template'], r['criterion'], r['statistic'])
        t[k] = float(r['tau_star'])
        if str(r.get('rule') or '').startswith('R0_VACUOUS_INTERNAL'):
            vac.add(k)
    return t, vac


def classify(exp, detected, measurable):
    """measurable=False ⇒ 这条工件**没有任何可判实例**或有实例但那一格没标定 τ*，
    那是 NA，不是漏检。把 NA 记成 MISS 会同时冤枉判据、也虚报覆盖率。"""
    if not measurable:
        return 'NA_NOINST'
    return {'detectable': ('TP', 'MISS'), 'blind': ('BLIND_BUT_FIRED', 'BLIND_CONFIRM'),
            'benign': ('FP', 'BENIGN_OK'), 'weak': ('WEAK_FIRED', 'WEAK_QUIET')} \
        .get(exp, ('UNKNOWN', 'UNKNOWN'))[0 if detected else 1]


def benign_certified():
    """良性类的**标签权威**是 `BENIGN_PROOF.csv`（自己报的数与闭式真值在 τ\\* 下一致），
    不是 `mutants.jsonl` 里那个手写的 expected。两者不一致时（历史上就是 E35 那 6 件）
    要单列一类报出来，而不是让它冒充 FP 或冒充 BENIGN_OK。"""
    if not os.path.exists(BEN):
        return None
    return {(r['task_id'], r['error_type']) for r in csv.DictReader(io.open(BEN, encoding='utf-8'))
            if r.get('verdict') == 'PROVES_BENIGN'}


def open_matrix(path):
    """支持 glob：分片各写自己的文件，汇总时合并 —— 并发追加同一个 CSV 太容易被一次 rm 打掉。"""
    import glob as _g
    files = sorted(_g.glob(path)) if any(c in path for c in '*?[') else [path]
    # ⚠ `MUTANT_MATRIX_R10b.shard*.csv` 这个 glob **同时**匹配到伴生的 `.triggers.csv`
    # （表头没有 stage/rel 列）。不排掉就是把触发表当矩阵读，症状是判据静默少一格。
    files = [f for f in files if '.triggers.' not in os.path.basename(f)]
    assert files, '没有匹配到矩阵文件：%s' % path
    hdr = None
    for fn in files:
        with io.open(fn, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if 'stage' not in r:
                    raise SystemExit('%s 不像矩阵文件（表头没有 stage 列）⇒ glob 抓错文件' % fn)
                yield r


def load_triggers(matrix_path):
    """读触发计数表（`run_mutant_matrix.py` 与矩阵同时产出，一片一文件）。

    没有这张表就**不做 IDLE 判定**（返回空表 ⇒ 后面一律按"无触发读数"处理并显式报数），
    绝不退回到"数与参照件相同 ⇒ 注入没跑"那种会把引理 C 的证据误删的推断。
    """
    import glob as _g
    stem = matrix_path[:-4] if matrix_path.endswith('.csv') else matrix_path
    files = sorted(_g.glob(stem + '.triggers.csv')) or sorted(_g.glob(
        os.path.join(HERE, 'MUTANT_MATRIX_R10*.triggers.csv')))
    out = {}
    for f in files:
        for r in csv.DictReader(io.open(f, encoding='utf-8')):
            k = (r['task_id'], r['error_type'])
            prev = out.get(k)
            if prev is not None and prev != r:
                raise SystemExit('触发表同一件两份不一致读数：%s vs %s（%s）' % (
                    prev, r, f))
            out[k] = r
    return out


def judge(matrix_path):
    TAU, VAC = load_tau()
    seen_ids = set()
    first_row = {}
    dup = []
    n_dup_ident = 0
    per_art = defaultdict(lambda: dict(num_A=False, num_B=False, crash=False,
                                       rows=0, no_tau=0, fired_cells=[], cells=[],
                                       evid_cells=0, vac_cells=0,
                                       xcheck_n=0, xcheck_bad=0, xcheck_eg=''))
    seeds = set()
    no_col = set()          # τ* 选档在矩阵里没有对应 `fired_<τ>` 列的格（见下面的硬失败）
    for r in open_matrix(matrix_path):
        k = (r['task_id'], r['error_type'])
        # 重复键**本身不是错**：分片与帮手进程会重做同一件。真正的错是"同一格两次跑出不同的数"
        # ⇒ 所以这里比的是整行内容：全等就安静去重，不等就把不一致的字段报出来（那是 nondeterminism）。
        uid = (r['key'], r['stage'], r.get('instance'), r.get('pert'), r.get('seeds'))
        body = tuple((kk2, vv) for kk2, vv in sorted(r.items()) if kk2 not in ('note',))
        if uid in seen_ids:
            if first_row.get(uid) != body:
                dup.append(uid)          # 同一格两次结果不一致 = nondeterminism，硬失败
            else:
                n_dup_ident += 1         # 全等重复（分片与帮手重做）⇒ 安静去重，只计首次
            continue
        seen_ids.add(uid)
        first_row[uid] = body
        seeds.add(r['seeds'])
        if r['stage'] == 'CRASH':
            per_art[k]['crash'] = True
            continue
        if r['stage'] == 'MISSING' or r['rel'] in ('', None):
            continue
        per_art[k]['rows'] += 1
        rel = float(r['rel'])
        crit = STAGE2CRIT.get(r['stage'])
        key = (r['template'], crit, r['instance'])
        ts = TAU.get(key)
        if ts is None:
            per_art[k]['no_tau'] += 1
            continue
        per_art[k]['num_A'] |= rel > ts
        if key in VAC:
            per_art[k]['vac_cells'] += 1        # 空判据格：照样交叉核对，但**不算独立证据**
        else:
            per_art[k]['evid_cells'] += 1
        if rel > ts:
            per_art[k]['fired_cells'].append('%s:%s rel=%.4g>τ*=%.3f' % (crit, r['instance'], rel, ts))
        # 逐观测量的**双向**记录（点火的与不点火的都留），量纲标本那一节要靠它
        per_art[k]['cells'].append('%s·%s rel=%.4f %s' % (
            crit, r['instance'], rel, '点火' if rel > ts else '不点火'))
        per_art[k]['num_B'] |= rel > 0.02
        # 交叉核对：我自己按 `rel` 重算的点火，必须等于矩阵里预先算好的 `fired_<τ>` 列。
        # ⚠ 这句话的能力有限，别再夸大（外部审计 P-07）：`fired_*` 列与这里的 `rel` **同源于同一次测量**
        # （`criteria.j5`…不，是 `criteria` 在写这行时同时给了 `rel` 与 `fired_at`），
        # 所以它**抓不到**"CSV 是旧引擎产的"或"criteria 的判据变了"——引擎变了两边一起变。
        # 它真正抓得到的是：τ\* 选档没落在矩阵的 grid 上、列名对不上、以及读写两侧的列错位。
        # 引擎新鲜度由另外两条腿承担：`check_recal_currency.py`（参照件残差）+
        # `AB_MATRIX_NO_SIDE_EFFECTS.md`（346 件在新引擎上整体重跑、逐格比 `rel`）。
        col = 'fired_%g' % ts
        if col not in r or r[col] in ('', None):
            no_col.add((r['template'], crit, r['instance'], ts))
            continue
        per_art[k]['xcheck_n'] += 1
        if int(r[col]) != int(rel > ts):
            per_art[k]['xcheck_bad'] += 1
            per_art[k]['xcheck_eg'] = '%s %s rel=%s 列%s=%s 我算=%d' % (
                r['task_id'], r['instance'], rel, col, r[col], int(rel > ts))
    if no_col:
        # τ* 选了个矩阵里没有的档 ⇒ 交叉核对会"静默少计数"（审计 P-07 的验收样本）。
        # 静默少计数比报错危险得多：报告照样印"不一致 0 格"，而那 0 是从更少的格上算的。
        raise SystemExit('有 %d 格（模板,判据,观测量,τ*）的 τ* 在矩阵里找不到 `fired_<τ>` 列，'
                         '例 %s ⇒ 要么 τ* 表与矩阵不同源，要么矩阵的 grid 少一档；'
                         '先对齐再出报告，不许静默跳过' % (
                             len(no_col), sorted(no_col)[:4]))
    return per_art, seeds, dup, len(seen_ids), n_dup_ident


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'MUTANT_MATRIX_R10.csv')
    import glob as _g0
    if not (_g0.glob(path) if any(c in path for c in '*?[') else [path]):
        raise SystemExit('矩阵不存在（或 glob 没匹配到文件）：%s' % path)
    exp = {}
    FAM = {}
    for line in io.open(MUT, encoding='utf-8'):
        m = json.loads(line)
        exp[(m['task_id'], m['error_type'])] = m['expected']
        FAM[(m['task_id'], m['error_type'])] = m.get('family', '')
    per_art, seeds, dup, n_rows, n_dup_ident = judge(path)
    if dup:
        raise SystemExit('矩阵里有 %d 行重复键（例 %s）⇒ 先查是谁在并发写/续跑键漏了什么，'
                     '重复行会让"任一观测量检出"被虚高' % (len(dup), dup[:2]))
    if seeds != {'10'}:
        print('[WARN] 本文件假设判定预算 = τ* 的标定预算 = 10 种子；矩阵里实际是 %s'
              ' ⇒ 若不一致，下面的数字仍是跨预算的，别引用' % sorted(seeds))
    cert = benign_certified()
    unproven = set()
    if cert is not None:
        unproven = {k for k, e in exp.items() if e == 'benign' and k not in cert}

    # ---- 注入空转判定（P-02/P-03）：只看这件自己那条机制的计数器 ----
    TRIG = load_triggers(path)
    trig_missing = trig_nocounter = 0

    def idle_state(kk):
        """返回 'IDLE' / 'LIVE' / 'NOCOUNTER' / 'NORUN'。后两种**不改判定身份**，只报数。"""
        gate = IDLE_GATE.get(kk[1])
        if not gate:
            return 'NOCOUNTER'
        r = TRIG.get(kk)
        if r is None or r.get('ran') != '1':
            return 'NORUN'                       # 崩了/没跑出来：矩阵那边已经是 CRASH/MISSING 档
        if kk[1] == 'E20' and str(r.get('trig_swap_noop')) == '1':
            return 'IDLE'                        # 两节点参数全同 ⇒ 换序是字面空操作
        try:
            vals = [float(r.get(g) or 0) for g in gate]
        except ValueError:
            return 'NORUN'
        return 'IDLE' if all(v == 0 for v in vals) else 'LIVE'

    IDLE_SET = set()
    for kk in exp:
        st = idle_state(kk)
        if st == 'IDLE':
            IDLE_SET.add(kk)
        elif st == 'NOCOUNTER':
            trig_nocounter += 1
        elif st == 'NORUN':
            trig_missing += 1

    def tally(det_of, mode):
        c = Counter()
        for k, e in exp.items():
            if e == 'benign' and k in unproven:
                c['BENIGN_UNPROVEN'] += 1      # 标了良性但自证闸没过：不进 FP 也不进 BENIGN_OK
                tag = 'BENIGN_UNPROVEN'
            elif k in IDLE_SET:
                c['INJECTION_IDLE'] += 1        # 机制没落地：既不算检出也不算漏检
                tag = 'INJECTION_IDLE'
            else:
                tag = classify(e, det_of(k, mode), meas(k))
                c[tag] += 1
            if mode == 'A':
                TAGS[k] = tag                   # 逐件判决要有可指认的载体，不能只活在 Counter 里
        return c

    def meas(k):
        a = per_art.get(k, {})
        return a.get('rows', 0) > 0 and a.get('no_tau', 0) < a.get('rows', 1)

    TAGS = {}
    res = {'A': tally(lambda k, m: bool(per_art.get(k, {}).get('num_A')), 'A'),
           'B': tally(lambda k, m: bool(per_art.get(k, {}).get('num_B')), 'B'),
           'A_crash': tally(lambda k, m: bool(per_art.get(k, {}).get('num_A')) or bool(per_art.get(k, {}).get('crash')), 'C')}
    tags_out = os.environ.get('MM_TAGS_OUT')
    if tags_out:
        tp = tags_out if os.path.isabs(tags_out) else os.path.join(HERE, tags_out)
        with io.open(tp, 'w', encoding='utf-8', newline='') as f:
            wr = csv.writer(f)
            wr.writerow(['task_id', 'error_type', 'template', 'family', 'expected_declared',
                         'tag_strict_A', 'fired_A', 'rows', 'no_tau', 'ran'])
            for k in sorted(TAGS):
                a = per_art.get(k, {})
                t = TRIG.get(k, {})
                wr.writerow([k[0], k[1], k[0].rsplit('-', 1)[0], FAM.get(k, ''),
                             exp.get(k, ''), TAGS[k],
                             int(bool(a.get('num_A'))), a.get('rows', 0), a.get('no_tau', 0),
                             t.get('ran', '')])
        emit('[mmatrix] 逐件判决表 → %s（%d 件）' % (os.path.basename(tp), len(TAGS)))
    if unproven:
        print('⚠ 标 benign 但未过自证闸的件 %d 件，错误类型 %s ⇒ 单列一类，不混进 FP/BENIGN_OK' % (
            len(unproven), sorted({k[1] for k in unproven})))

    d_strict = res['A'].get('TP', 0) + res['A'].get('MISS', 0) + res['A'].get('NA_NOINST', 0)
    d_meas = res['A'].get('TP', 0) + res['A'].get('MISS', 0)
    dC = res['A_crash'].get('TP', 0) + res['A_crash'].get('MISS', 0)
    blA = res['A'].get('BLIND_CONFIRM', 0) + res['A'].get('BLIND_BUT_FIRED', 0)
    nb = len(cert) if cert is not None else sum(1 for v in exp.values() if v == 'benign')
    L = ['# 变异体主矩阵汇总 v2（逐格 τ\\*，判定预算 %s 种子）\n' % sorted(seeds)]
    # 输入清单（审计 P-17：上一版报告由一次没留档的调用产生，且它的第 5 个输入 shard4b 已不在盘上
    # ⇒ 报告不可从交付物再生）。现在把"这份报告吃的是哪些文件、各多少行、什么时候写的、什么命令"写进正文。
    import glob as _gm
    import time as _tm
    ins = sorted(_gm.glob(path)) if any(c in path for c in '*?[') else [path]
    L.append('## 输入清单（再生这份报告需要且仅需要这些）')
    L.append('')
    for fn in ins:
        # ⚠ 行数 ≠ 记录数（末尾少一个换行就少报 1 条，这条今天已经记过一次，还在别处犯）：
        #    CSV 一律用 DictReader 数记录。
        n = sum(1 for _ in csv.DictReader(io.open(fn, encoding='utf-8')))
        L.append('- `%s`  数据行 %d  mtime %s' % (
            os.path.basename(fn), n, _tm.strftime('%Y-%m-%d %H:%M', _tm.localtime(
                os.path.getmtime(fn)))))
    tfn = sorted(_gm.glob(os.path.splitext(path)[0] + '.triggers.csv')) if any(
        c in path for c in '*?[') else []
    for fn in tfn:
        L.append('- `%s`（触发表）数据行 %d' % (os.path.basename(fn), sum(
            1 for _ in csv.DictReader(io.open(fn, encoding='utf-8')))))
    L.append('- 命令：`%s`' % ' '.join(['summarize_matrix_v2.py'] + sys.argv[1:]))
    L.append('- τ\\* 来源：`table_tau_v2.csv`（%d 行有 τ 星）；良性权威：`%s`' % (
        len(load_tau()[0]), os.path.basename(BEN)))
    L.append('')
    cov = sum(1 for k in exp if per_art.get(k, {}).get('rows', 0) > 0)
    L.append('- 工件数：%d（`mutants.jsonl`）；**有判定行的件：%d**（差 %d 件＝整件无可判行）；'
             '唯一格 %d、**重复但逐字段全等 %d 格**（分片与帮手进程重做同一件，已安静去重）；'
             '有崩溃行的件：%d' % (
                 len(exp), cov, len(exp) - cov, n_rows, n_dup_ident,
                 sum(1 for a in per_art.values() if a['crash'])))
    if cov != len(exp):
        L.append('  [WARN] 覆盖不全 ⇒ 要么分片没跑完，要么这些件的字段契约缺失。**先补齐再引用任何比率**。')
    # **空判据不进"独立判据"计数**（2026-10-18，第四轮 R4 后半句：我只做到"能标记"没做到"能剔除"）。
    # `R0_VACUOUS_INTERNAL` = 参照件上恒为 0 且理由是定义（`J2c=max(0,busy_frac−1)`，而忙度 ≤1 由定义成立）。
    n_ev = sum(a.get('evid_cells', 0) for a in per_art.values())
    n_vc = sum(a.get('vac_cells', 0) for a in per_art.values())
    L.append('- 带 τ\\* 的实测格：**独立证据格 %d** + **空判据格 %d**（矩阵里落在 '
             '`rule=R0_VACUOUS_INTERNAL` 那些格上的实测行）⇒ 空判据格**只用于交叉核对，'
             '不许写进"守恒律/恒等类由 N 条判据支撑"**；它们对外部工件仍有效（模型可能把忙度算成 >1、'
             '或把窗口报出可行域），所以留着但不计证据。τ 表里被标为空的格：%s'
             '（其中 `J0*` 不进主表，所以主表矩阵里它们的实测行数为 0）' % (
                 n_ev, n_vc, ', '.join('%s/%s' % (k[0], k[2]) for k in sorted(load_tau()[1]))[:200]))
    # **题集覆盖度**（2026-10-17 我自己补的一条，外部审计没抓到）：主表是"错型语料"，
    # 它只覆盖被注入的那部分题，不是 64 题全覆盖。谁写"语料覆盖 64 题"就是假的。
    n_task_mat = len({k[0] for k in exp if per_art.get(k, {}).get('rows', 0) > 0})
    try:
        n_task_all = sum(1 for l in io.open(os.path.join(HERE, 'tasks.jsonl'), encoding='utf-8')
                         if l.strip())
    except IOError:
        n_task_all = 0
    by_tpl_task = defaultdict(set)
    for k in exp:
        if per_art.get(k, {}).get('rows', 0) > 0:
            by_tpl_task[k[0].rsplit('-', 1)[0]].add(k[0])
    L.append('- **题集覆盖：%d/%d 题**（按模板 %s）⇒ 主表的口径是"错型 × 题（被注入的那些）"，'
             '不是 64 题全语料；`P0_CROSSCHECK.csv` 才是 64 题都过的那道闸。' % (
                 n_task_mat, n_task_all,
                 ', '.join('%s %d' % (t, len(v)) for t, v in sorted(by_tpl_task.items()))))
    L.append('- 标签**直接照 `mutants.jsonl`**，本脚本不再挂重标字典（那份 `RELABEL` 已过期，'
             '而且两条错型的下场不同：`E28` 在发射器上被做成真良性、由 `BENIGN_PROOF.csv` 自证；'
             '`E35` 只换输入侧口径 ⇒ 10-17 改判 detectable，**不在**良性认证里）。')
    idle_by_tpl = Counter(k[1] for k in IDLE_SET)
    L.append('- **注入空转（机制计数器全 0）：%d 件** ⇒ 单列 `INJECTION_IDLE`，'
             '既不进"盲区证实"的分子分母，也不进"漏检"；按错型 %s。'
             '另：无触发计数器的错型 %d 件、跑不出读数的 %d 件（这两种**不改变判定身份**，只报数）。' % (
                 len(IDLE_SET), json.dumps(dict(idle_by_tpl), ensure_ascii=False),
                 trig_nocounter, trig_missing))
    if not TRIG:
        L.append('  [WARN] 没有触发表（`*.triggers.csv`）⇒ 本轮**未做**空转判定，'
                 '恒等类分母的口径退回"仅按读数判"，引用时要写明。')
    L.append('- 空转件逐条：%s' % (', '.join('%s/%s' % k for k in sorted(IDLE_SET)) or '无'))
    xn = sum(a['xcheck_n'] for a in per_art.values())
    xb = sum(a['xcheck_bad'] for a in per_art.values())
    eg = next((a['xcheck_eg'] for a in per_art.values() if a['xcheck_bad']), '')
    L.append('- 与矩阵里 `fired_<τ\\*` 列**交叉核对**：%d 格可比，不一致 **%d** 格%s' % (
        xn, xb, ('' if not xb else '，例：%s' % eg)))
    L.append('  [WARN] 这条核对**抓不到引擎漂移**：`rel` 与 `fired_*` 来自同一次测量，引擎变了两边一起变。'
             '它能抓的是 τ\\* 档位不在矩阵 grid 上、列名错位（后者现在是硬失败，不再静默少计数）。'
             '引擎新鲜度的两条腿是 `check_recal_currency.py`（参照件）与 '
             '`AB_MATRIX_NO_SIDE_EFFECTS.md`（346 件在新引擎上整体重跑）。')
    if cert is not None:
        L.append('- 良性类以 `BENIGN_PROOF.csv` 为标签权威：认证通过 %d 件；'
                 '标了 benign 但没过自证 **%d 件**（%s），单列为 `BENIGN_UNPROVEN`，不混进 FP 也不混进 BENIGN_OK。' % (
                     len(cert), len(unproven), sorted({k[1] for k in unproven}) or '-'))
    L.append('')
    L.append('| 类别 | A 逐格τ\\*（数值） | B 全局 0.02（旧做法） | A+崩 |')
    L.append('|---|---|---|---|')
    for t in TAGS:
        L.append('| %s | %d | %d | %d |' % (t, res['A'].get(t, 0), res['B'].get(t, 0), res['A_crash'].get(t, 0)))
    L.append('')
    L.append('## 分母有三套，不许混用')
    L.append('- **严格**（所有标为 detectable 的件）= %d；**可判**（至少有一格带 τ\\* 且实测到数）= %d；'
             '两者差 %d 件 = 无可判实例（`NA_NOINST`）。' % (d_strict, d_meas, res['A'].get('NA_NOINST', 0)))
    L.append('')
    L.append('## 三条摘要话')
    L.append('- 理论说可检：**可判分母下 %d/%d = %.1f%%**，严格分母下 %d/%d = %.1f%%；'
             '旧做法（全局 0.02）%d/%d ⇒ 规则差异影响 %d 件。' % (
                 res['A'].get('TP', 0), d_meas, 100.0 * res['A'].get('TP', 0) / max(1, d_meas),
                 res['A'].get('TP', 0), d_strict, 100.0 * res['A'].get('TP', 0) / max(1, d_strict),
                 res['B'].get('TP', 0), res['B'].get('TP', 0) + res['B'].get('MISS', 0),
                 abs(res['A'].get('TP', 0) - res['B'].get('TP', 0))))
    L.append('- 理论说不可检（恒等类）%d 件：A 下 %d 件全程不点火 = %.1f%%，例外 %d 件。' % (
        blA, res['A'].get('BLIND_CONFIRM', 0), 100.0 * res['A'].get('BLIND_CONFIRM', 0) / max(1, blA),
        res['A'].get('BLIND_BUT_FIRED', 0)))
    L.append('- 良性对照 %d 件：A 下误杀 %d 件；0/%d 的 95%% Wilson 上界 = %.1f%%。'
             '⇒ 只能说"这批里没误杀"，不能说"判据没有假阳"（假阳率是判据×预算的属性，见 `GATE_R10.md`）。' % (
                 nb, res['A'].get('FP', 0), nb, 100.0 * wilson_upper0(nb)))
    L.append('')
    def A_det(k):
        return bool(per_art.get(k, {}).get('num_A'))
    # ⚠ 逐件清单必须和上面那张表用**同一套**剔除规则：IDLE 件不进分子分母，也不该出现在
    #    "MISS（N 件）"这种小节标题里。23:1x 那份报告就是栽在这里——表里 `MISS 0`，
    #    下面的小节却印 `## MISS（2 件）`（正是被剔成 IDLE 的 `mmcK-06/E03、/E24`），
    #    一份自相矛盾的交付物，外部审查一眼就能拿这句反问我。
    miss = [k for k, e in exp.items() if k not in unproven and k not in IDLE_SET
            and classify(e, A_det(k), meas(k)) == 'MISS']
    bb = [k for k, e in exp.items() if k not in unproven and k not in IDLE_SET
          and classify(e, A_det(k), meas(k)) == 'BLIND_BUT_FIRED']
    fp = [k for k, e in exp.items() if k not in unproven and k not in IDLE_SET
          and classify(e, A_det(k), meas(k)) == 'FP']
    for tag, lst in (('MISS', miss), ('BLIND_BUT_FIRED', bb), ('FP', fp)):
        L.append('## %s（%d 件%s）' % (tag, len(lst),
                                      '' if lst else '，且已剔除 %d 件 INJECTION_IDLE' % len(IDLE_SET)))
        for k in lst:
            a = per_art.get(k, {})
            L.append('  %s %s crash=%s rows=%d 无τ*的格=%d  %s' % (
                k[0], k[1], a.get('crash'), a.get('rows', 0), a.get('no_tau', 0),
                ' | '.join(a.get('fired_cells', [])[:2])))
        L.append('')
    # 出报告前的自检：小节里的逐件清单条数必须等于上面那张表的条数（同一份文件里
    # "表说 0、正文小节说 2"这种自相矛盾，不该留给外部审查去发现）。
    for tag, lst in (('MISS', miss), ('BLIND_BUT_FIRED', bb), ('FP', fp)):
        n_tab = res['A'].get(tag, 0)
        assert n_tab == len(lst), \
            ('报告自相矛盾：分类表 %s=%d，逐件小节列了 %d 件 ⇒ 两处的剔除规则不同源'
             % (tag, n_tab, len(lst)))
    no_tau = {k: v['no_tau'] for k, v in per_art.items() if v['no_tau']}
    if unproven:
        L.append('## `BENIGN_UNPROVEN` 这组不是"标错了"，是论文的一条结果')
        L.append('这组是"`mutants.jsonl` 标了 benign、但 `BENIGN_PROOF.csv` 没认证通过"的件：'
                 '量纲类错型（同倍换单位）在**不变量观测量**上 rel=0、在**带量纲的观测量**上 rel≈1，'
                 '所以它既不能当良性对照（判据要抓它），也不能当可检类（错不在决策上）。'
                 '逐观测量表现（现算）：')
        for k in sorted(unproven):
            L.append('  - %s %s：%s' % (k[0], k[1], '；'.join(per_art.get(k, {}).get('cells', [])[:6])))
        L.append('⇒ 可写的句子：**同一件"良性"改写，在不变量观测量上 rel=0、在带量纲的观测量上 rel≈1** '
                 '⇒ "良性/非良性"不是工件的属性，是（错型 × 观测量）的属性。\n')
    L.append('## 未标定的 (模板,判据,观测量) 组合（**不给默认阈值**）')
    L.append('- 涉及 %d 件、共 %d 格。要么补标定，要么在论文里把这些格标为"未标定"，不许用默认值顶。' % (
        len(no_tau), sum(no_tau.values())))
    txt = '\n'.join(L)
    # 输出路径可由 MM_OUT 指走：预览/重算不许覆盖当前权威汇总（规矩 15）
    io.open(os.environ.get('MM_OUT') or os.path.join(HERE, 'MUTANT_SUMMARY_v2.md'),
            'w', encoding='utf-8').write(txt + '\n')
    emit(txt)


if __name__ == '__main__':
    main()
