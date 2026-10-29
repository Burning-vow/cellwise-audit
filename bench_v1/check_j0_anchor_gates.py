"""J0 单位锚的验收闸（2026-10-18，`selfcheck_all` 第 16 项）。

J0 是干什么的：工件自己声明的 `time_unit` / `runtime_units` 是**能挪的门柱**——
`J2a`(Little) 与 `J3a`(PASTA) 的换算都读它。10-17 实测过钉死单位的代价
（`UNIT_HEALING_EXPOSURE.md`：14 件诚实换单位的 E28 会把 J2a 从 1e-5 顶到 0.9833，
也就是**把真良性件打成假阳**）。所以正确的加固是加一条**工件改不掉的锚**
（题面给的 λ × 窗口长度 对 `arr`），而不是去掉自愈。

这道闸两头都要有样本（规矩 21：只有负样本的闸挡不住"太严"这一族错）：
  正向对照：诚实件、以及**诚实换单位**的 E28 ⇒ J0 三条腿都不许响；
  负样本：谎报 `runtime_units` / 谎报 `time_unit` 成词表外的生词 / `dep_rate` 与 `dep`、`win`
          自相矛盾 ⇒ 必须响在**指定的那一条腿**上；
  NA 语义：字段不齐 ⇒ 记 `field_missing` 且**不算响**（不许误伤）；
           单位是生词 ⇒ 必须显式记 `unknown_unit`，且 J2a/J3a 一起变成 NA，
           **绝不允许"默认当小时"算出一个数来冒充通过**（10-18 之前就是这样的）。

不碰任何交付件：只跑 `artifacts/*__REF.py`、`artifacts/mm1-02__E28.py` 取真读数，
谎报样本全部是在内存里改读数字典（改的是"工件声称了什么"，不是判据本身）。
"""
import csv
import io
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C   # noqa: E402

ART = os.path.join(HERE, 'artifacts')
# 写报告的路（负样本把它指到 temp）。⚠ 它与自检器**读**报告的那个口子必须分开：
# 同一个口子会让自检在判分前先把坏样本覆盖成干净报告，负样本于是"永远不响"（半个门禁）。
OUT = os.environ.get('J0AG_OUT') or os.path.join(HERE, 'J0_ANCHOR_GATES.md')
TID = 'mm1-02'
SEEDS, HOR = 10, 40000.0          # 与 τ* 标定同一口径，否则这道闸验的不是生产配置
STRICT = min(C.TAU_GRID)          # 0.01：最严那一档都不许响，才算"诚实件不响"


def emit(s):
    try:
        sys.stdout.write(s + '\n')
    except UnicodeEncodeError:
        sys.stdout.buffer.write(str(s).encode('utf-8', 'replace') + b'\n')


def run(name):
    path = os.path.join(ART, '%s__%s.py' % (TID, name))
    obs, dt, note = C.run_artifact(path, SEEDS, HOR, 'none', 1)
    assert obs is not None, '跑不出读数：%s（%s）' % (path, str(note)[-120:])
    return obs


def j0(obs, task):
    """`horizon` 传的是**判分器自己的调用参数** —— J0e 这条腿的强度全在这里。"""
    return C.j0_unit_anchor(obs, task, tau=STRICT, horizon=HOR)['per_stat']


def rel_of(d):
    return d.get('rel')


def main():
    task = next(t for t in C.load_tasks() if t['task_id'] == TID)
    ref = run('REF')
    e28 = run('E28')
    L = ['# J0 单位锚验收（`check_j0_anchor_gates.py` 产生）', '',
         '生成时间：%s ｜ 题 %s ｜ 口径 seeds=%d horizon=%g（与 τ* 标定一致）｜ 最严档 τ=%g' % (
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'), TID, SEEDS, HOR, STRICT), '',
         '| 用例 | 改了什么 | J0a 计数-窗口 | J0b 率-窗口 | J0c 率-题面λ | **J0e 窗口-调用参数** | 期望 | 判定 |',
         '|---|---|---|---|---|---|---|---|']
    fails = []

    def cell(d, k):
        v = d.get(k) or {}
        r = rel_of(v)
        return ('NA:' + str(v.get('status', ''))[:26]) if r is None else ('%.4g' % r)

    def case(label, obs, changed, expect):
        """expect = {腿名: ('fire'|'quiet'|'na_unknown'|'na_missing', 可选说明)}"""
        d = j0(obs, task)
        legs = ('J0a_arrival_lambda', 'J0b_rate_flow', 'J0c_rate_lambda', 'J0e_win_invocation')
        rows = [cell(d, k) for k in legs]
        bad = []
        for leg, (kind, _why) in expect.items():
            v = d.get(leg) or {}
            r = rel_of(v)
            st = str(v.get('status', ''))
            if kind == 'fire' and not (r is not None and r > STRICT and v.get('fired')):
                bad.append('%s 该响但 rel=%s' % (leg, r))
            if kind == 'quiet' and not (r is not None and r <= STRICT):
                bad.append('%s 不该响但 rel=%s status=%s' % (leg, r, st))
            if kind == 'na_unknown' and not (r is None and 'unknown_unit' in st):
                bad.append('%s 该记 unknown_unit 但 status=%r rel=%s' % (leg, st, r))
            if kind == 'na_missing' and not (r is None and 'field_missing' in st):
                bad.append('%s 该记 field_missing 但 status=%r rel=%s' % (leg, st, r))
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s |' % (
            label, changed, rows[0], rows[1], rows[2], rows[3],
            '、'.join('%s:%s' % (k.split('_')[0], v[0]) for k, v in sorted(expect.items())),
            'OK' if not bad else 'FAIL：' + '；'.join(bad)))
        if bad:
            fails.append('%s：%s' % (label, '；'.join(bad)))
        return d

    # 1) 正向对照：诚实参照件
    case('诚实件', ref, '不动', {
        'J0a_arrival_lambda': ('quiet', 'arr 对题面 λ×win'),
        'J0b_rate_flow': ('quiet', 'dep_rate×win 对 dep'),
        'J0c_rate_lambda': ('quiet', 'dep_rate 对 λ(1−p_loss)'),
        'J0e_win_invocation': ('quiet', 'win 落在调用允许区间内')})

    # 2) 正向对照：诚实换单位（E28 把率、时域、输出口径一起换成分钟）⇒ 锚不许响
    case('诚实换单位 E28', e28, 'λ、μ、horizon、输出口径同步 ×60（内部自洽）', {
        'J0a_arrival_lambda': ('quiet', '两边同步 ⇒ 不响'),
        'J0b_rate_flow': ('quiet', '两边同步 ⇒ 不响'),
        'J0c_rate_lambda': ('quiet', 'time_unit=minute 认得'),
        'J0e_win_invocation': ('quiet', '1.8e6 分钟折回 30000 小时 ⇒ 在区间内')})

    # 2b) J0e 的**区间边界**样本：把窗口强行设成合法预热值的两个端点（0 与 0.5）。
    #     注意这里只改 `win`，所以 J0a/J0b 会响（物理上不诚实）——**这两行只对 J0e 有意义**。
    #     为什么要它：恒等式 `win+warmup_units=horizon` 会在这里造假阳（`warmup_units` 是内核
    #     发的常量，见 `criteria.W_WINDOW_MAX` 那段），而真实 E26/E30 的读数我另跑一遍验。
    for nm, wv in (('J0e 上界 win=horizon(等价 E26 的窗口)', HOR),
                   ('J0e 下界 win=horizon×(1−0.5)(等价 E30)', HOR * (1 - C.W_WINDOW_MAX))):
        lie = dict(ref)
        lie['win'] = wv
        case('区间端点 %s' % nm, lie, '只把 win 设成 %g（此行为**只判 J0e**，J0a/J0b 响是预期的）' % wv, {
            'J0e_win_invocation': ('quiet', '落在闭区间端点上')})

    # 3) 负样本 1：谎报 runtime_units（数值还是小时口径，声明成分钟）⇒ J0a 必响，J0e 也跟着响
    lie = dict(ref)
    lie['runtime_units'] = 'minute'
    case('谎报 runtime_units', lie, "runtime_units='minute' 而 win/arr 没变", {
        'J0a_arrival_lambda': ('fire', 'λ·win·h 挪 60 倍，arr 动不了'),
        'J0b_rate_flow': ('quiet', '这条腿不吃 runtime_units'),
        'J0c_rate_lambda': ('quiet', '这条腿吃 time_unit，不受影响'),
        'J0e_win_invocation': ('fire', '折成小时后只剩 500，低于下界')})

    # 4) 负样本 2：time_unit 写成词表外的生词 ⇒ J0c 记 unknown_unit，且 J2a/J3a 必须一起 NA，
    #    并且**必须留下 unit_violation 痕迹**（NA ≠ 安全，它是失声；腿 B 靠这条才看得见）
    lie = dict(ref)
    lie['time_unit'] = 'fortnight'
    d = case('生词 time_unit', lie, "time_unit='fortnight'（词表外）", {
        'J0a_arrival_lambda': ('quiet', '锚的是 arr，不吃 time_unit'),
        'J0c_rate_lambda': ('na_unknown', '不许默认当小时'),
        'J0e_win_invocation': ('quiet', '这腿吃 runtime_units')})
    j2 = (C.j2_conservation(lie, task, tau=STRICT)['per_stat'] or {}).get('J2a_little', {})
    j3 = (C.j3_pairing(lie, task, tau=STRICT)['per_stat'] or {}).get('J3a_util_pasta', {})
    for nm, x in (('J2a_little', j2), ('J3a_util_pasta', j3)):
        if x.get('rel') is not None or 'unknown_unit' not in str(x.get('status', '')):
            fails.append('生词 time_unit 下 %s 没有变 NA：rel=%s status=%r ⇒ "自愈门柱"还开着' % (
                nm, x.get('rel'), x.get('status')))
        L.append('| ↳ 连带检查 %s | 同上 | rel=%s，status=%s | | | | 必须 NA(unknown_unit) | %s |' % (
            nm, x.get('rel'), x.get('status'),
            'OK' if (x.get('rel') is None and 'unknown_unit' in str(x.get('status', ''))) else 'FAIL'))
    uv = (C.j0_unit_anchor(lie, task, tau=STRICT, horizon=HOR) or {}).get('unit_violation') or []
    if not uv:
        fails.append('unit_violation 没留痕 ⇒ 腿 B 里"一个生词关掉四条判据"是隐形的（R4-4）')
    L.append('| ↳ 违规留痕 unit_violation | 同上 | | | | | 非空（把失声记成一次口径违规） | %s |' % (
        'OK：%s' % (uv[:1] or '') if uv else 'FAIL'))

    # 5) 负样本 3：dep_rate 与 dep、win 自相矛盾（率乘 2）⇒ J0b 必响，另外两条腿不该被牵连
    lie = dict(ref)
    lie['dep_rate'] = ref['dep_rate'] * 2.0
    case('率与计数矛盾', lie, 'dep_rate ×2 而 dep/win 不变', {
        'J0b_rate_flow': ('fire', 'dep_rate×win 对不上 dep'),
        'J0a_arrival_lambda': ('quiet', '不吃 dep_rate')})

    # 6) NA 语义：缺字段 ⇒ 记 field_missing，绝不算响（误伤良性件的那种"太严"错要在这里露）
    lie = dict(ref)
    lie.pop('arr')
    case('缺 arr', lie, '删掉 arr 字段', {
        'J0a_arrival_lambda': ('na_missing', '字段不齐要看得见，但不算报警'),
        'J0b_rate_flow': ('quiet', '另外两条腿照常')})

    # 7) 两件一起撒谎：`runtime_units` 与 `win` 同时改（×1/60 声明 + win×60）
    #    ⇒ J0a 被凑平；但只改这两个字段时 `dep_rate×win≈dep` 这条内部账露馅 ⇒ J0b 响。
    #    ⚠ 这只覆盖"**不同步**的合谋"。四条一起改（见下一行）本来就是合法的"内部用分钟"写法，
    #       那种情形 J0b 也静默是**正确行为**，不能拿它当"锚失效"的证据。
    lie = dict(ref)
    lie['runtime_units'] = 'minute'
    lie['win'] = ref['win'] * 60.0
    case('两字段合谋(不同步)', lie, "runtime_units='minute' 且 win ×60（想凑回 arr）", {
        'J0a_arrival_lambda': ('quiet', '这条腿确实被凑回来了'),
        'J0b_rate_flow': ('fire', '但 dep_rate×win 与 dep 的账露馅')})

    # 8) 反面：少报一个字段**不许**变成报警。J0c 的预测里有 `λ(1−p_loss)`，
    #    原先 `p_loss` 缺失被 `or 0.0` 当 0 ⇒ 有丢失的系统会拿错预测去比，等于仪器自己造假阳。
    #    （52 道排队题的 REF 全都报 p_loss，所以这条不是假设：它是腿 B 工件的真实形状。）
    lie = dict(ref)
    lie.pop('p_loss')
    case('缺 p_loss', lie, '删掉 p_loss 字段', {
        'J0a_arrival_lambda': ('quiet', '这条腿不吃 p_loss'),
        'J0c_rate_lambda': ('na_missing', '少了字段要记 NA，不许当 0 去比')})

    # 9) 【第四轮 R4-1 的构造】纯编造计数 + 反算：`arr` 改成任意值，
    #    再令 `win=arr/(λ·h)`、`dep_rate=dep/win` ⇒ J0a/J0b/J0c **三条自报腿全部归零**，
    #    连 J1 的闭式比对也不响（业务量 W/L 照抄诚实值）。⇒ J0 检的是自洽，不是真实。
    #    只有 `J0e`（窗口对**调用参数**）接得住，因为工件改不动我传进去的 horizon。
    lam = float(task['params']['lambda'])
    h = C._unit_hours_strict(ref['runtime_units'])
    for mult in (0.1, 2.0):
        lie = dict(ref)
        lie['arr'] = ref['arr'] * mult
        lie['dep'] = ref['dep'] * mult * (1 - (ref.get('p_loss') or 0.0))
        lie['win'] = lie['arr'] / (lam * h)
        lie['dep_rate'] = lie['dep'] / lie['win']
        case('反算凑平 arr×%g' % mult, lie,
             'arr=%g、win=arr/(λ·h)=%g、dep_rate=dep/win（三腿全被凑平）' % (lie['arr'], lie['win']), {
            'J0a_arrival_lambda': ('quiet', '被反算凑平了 ⇒ 这腿检的是自洽'),
            'J0b_rate_flow': ('quiet', '同样被凑平'),
            'J0c_rate_lambda': ('quiet', '同样被凑平'),
            'J0e_win_invocation': ('fire', '窗口折成小时后跑出 [20000,40000] ⇒ 这腿是外部锚')})

    # 10) 【真实良性标本的正向对照】直接跑 E26（不预热）与 E30（预热一半）两件工件，
    #     四条腿必须**全部不响**。上一轮我因为"把合法口径的两种写法当假设"被外部复算打过一次，
    #     这次要盘上产物，不要嘴上的"应该没问题"。
    for nm in ('e26', 'e30'):
        obs = run(nm)
        case('真实良性件 %s' % nm.upper(), obs, '整件真跑（窗口占比 0 / 0.5，arr/dep 跟着窗口一起变）', {
            'J0a_arrival_lambda': ('quiet', '窗口变但 λ 不变 ⇒ 计数也同比变，仍自洽'),
            'J0b_rate_flow': ('quiet', '同上'),
            'J0c_rate_lambda': ('quiet', '同上'),
            'J0e_win_invocation': ('quiet', '窗口正是调用参数允许的两种取值')})

    # 11) 接线检查：J0 必须真的进了标定与 stage1 两条生产路（不然这只是个玩具函数）
    src_recal = io.open(os.path.join(HERE, 'run_recal64.py'), encoding='utf-8').read()
    src_stage = io.open(os.path.join(HERE, 'run_p0_crosscheck.py'), encoding='utf-8').read()
    for nm, hay in (('run_recal64.py（标定）', src_recal), ('run_p0_crosscheck.py（stage1）', src_stage)):
        if 'j0_unit_anchor' not in hay:
            fails.append('%s 里没有调用 j0_unit_anchor ⇒ 锚没接进生产路' % nm)
        L.append('| ↳ 接线 %s | — | — | — | — | — | 源码含 j0_unit_anchor | %s |' % (
            nm, 'OK' if 'j0_unit_anchor' in hay else 'FAIL'))
    # 表里有没有 J0 行：**只在已经重跑过之后才要求**，重跑前的旧表不算不一致（新增键不算冲突）
    tp = os.path.join(HERE, 'table_tau_v2.csv')
    if os.path.exists(tp):
        rows = list(csv.DictReader(io.open(tp, encoding='utf-8')))
        n_j0 = sum(1 for r in rows if r['criterion'] == 'J0')
        L.append('- `table_tau_v2.csv` 里 criterion=J0 的行：%d（0 = 标定链还没在新判据上重跑，'
                 '此时 stage1 会把 J0 记成 `no_tau` 而**不给默认阈值**）' % n_j0)
        if n_j0:
            none_tau = [r for r in rows if r['criterion'] == 'J0' and r['tau_star'] in ('', 'NONE')]
            if none_tau:
                fails.append('J0 已进表但有 %d 行没有 τ*（%s）⇒ 要么补标定，要么正文别引用' % (
                    len(none_tau), sorted({r['template'] for r in none_tau})))
            L.append('- 有 τ* 的 J0 行覆盖模板：%s，缺 τ*：%s' % (
                sorted({r['template'] for r in rows if r['criterion'] == 'J0'
                        and r['tau_star'] not in ('', 'NONE')}),
                sorted({r['template'] for r in none_tau}) or '无'))
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    for f in fails:
        emit('FAIL：' + f)
    emit('[j0_anchor] %s（%d 条失守），报告 J0_ANCHOR_GATES.md' % (
        'PASS' if not fails else 'FAIL', len(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
