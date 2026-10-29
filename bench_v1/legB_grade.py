"""腿 B 判分用的**一条**观测量出口：排队侧 J1 + 库存侧 J1inv 都要走到。

为什么单独成一个模块（而不是就地各写一遍）：
`criteria.j1_analytic` 只遍历 `OBSERVABLES = (W, L, p_loss, busy_frac, p_wait)`，
库存题的真值是 `q / exp_profit / cost`——腿 A 早就知道这件事，专门写了 `inv_obs.j1_inv`，
它的模块说明原话是"照原样跑的话，报童/EOQ 的 60 个变异件会一个可判实例都没有、静默从主表里消失"。
我的腿 B 探针和回判脚本**只调了 j1_analytic**，于是同一个坑在这儿再犯一次：
eoq/newsvendor 的工件即便字段齐全，`cells` 也是空的 ⇒ 既不算"一致"也不算"不一致"，
而汇总里只看 `n_agree`，就把它当成"模型没做对"记进 0% 里了。⇒ 那是**仪器缺器官**，不是模型缺陷。

所以这里把两条出口合成一条，probe / rejudge 共用，判分出口只留一个。
τ 星（逐格阈值）仍从 `table_tau_v2.csv` 取（criterion='J1'，statistic 用各自的观测量名）。

字段契约也住在这一份里（`required_fields` / `contract_fields`），`gen_legB` 只是转过来调用：
判"缺字段"的依据和"能比哪些观测量"的依据必须是同一个来源，否则又变成两条出口各说一套。
"""
import csv
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C                                    # noqa: E402
from inv_obs import j1_inv, INV_OBS                      # noqa: E402

TAU_CSV = os.environ.get('SC_TAU_CSV') or os.path.join(HERE, 'table_tau_v2.csv')
CONTRACT_CSV = os.environ.get('SC_CONTRACT_CSV') or os.path.join(HERE, 'field_contract.csv')
ART_DIR = os.path.join(HERE, 'artifacts')
SEEDS, HOR = 10, 40000.0        # 与 τ* 的标定预算一致；腿 B 所有判分/探针/回判共用这一口径


def pick_tasks(n, only_with_ref=True):
    """按模板轮转取样，保证 9 个模板都被覆盖，而不是前 n 道题全落在 mm1 上。"""
    tasks = C.load_tasks()
    if only_with_ref:
        refs = {t['task_id'] for t in tasks
                if os.path.exists(os.path.join(ART_DIR, '%s__REF.py' % t['task_id']))}
        tasks = [t for t in tasks if t['task_id'] in refs]
    by_tpl = {}
    for t in tasks:
        by_tpl.setdefault(t['template'], []).append(t)
    out, i = [], 0
    while len(out) < n and any(len(v) > i for v in by_tpl.values()):
        for tpl in sorted(by_tpl):
            if i < len(by_tpl[tpl]):
                out.append(by_tpl[tpl][i])
                if len(out) == n:
                    break
        i += 1
    return out[:n]


# 口径自述字段：判分靠它们核对预算与时间轴，缺一个就不能算"可比"。
META = ('time_unit', 'seeds_used', 'seed_list', 'win', 'runtime_units')
# 恒等式判据（J2/J3）要吃的观测量。这份清单**只用来决定 prompt 里"建议一并报出"那一段**，
# 不进"缺字段"的判定；缺失的后果是对应判据记"不可比"，不是白送通过。
# 下面 `_assert_ident_fields_read()` 会逐个核对这些名字确实出现在 criteria.py 源码里，
# 判据改了字段名而这里没改，就会当场炸而不是静默少要字段。
IDENT_FIELDS = ('arr', 'dep', 'blk', 'dep_rate', 'busy_frac', 'busy_util', 'p_loss',
                'p_wait', 'lam_eff')
# 仪器内部的机制计数器（simcore.contract_out 里加的）：参照件会报它们，但它们是**我这边的读数**，
# 绝不能进 prompt、也不能进"缺字段"判定。清单以外的 `trig_` 键出现 = 内核加了新计数器而这里没跟上，
# 直接停下（外部审计 F-6 那一族：交付物里多一个"长得像模型输出"的列）。
INSTRUMENT_KEYS = frozenset(('trig_nonhead', 'trig_preempt', 'trig_class0',
                             'trig_transfer', 'trig_swap_noop'))
_CONTRACT = {}


def _assert_ident_fields_read():
    src = io.open(os.path.join(HERE, 'criteria.py'), encoding='utf-8').read()
    dead = [f for f in IDENT_FIELDS if ("'%s'" % f) not in src and ('"%s"' % f) not in src]
    assert not dead, 'IDENT_FIELDS 里有 criteria.py 根本不读的字段名 %s ⇒ 判据改过，清单要跟着改' % dead


def tau_map():
    """(template, statistic) -> τ*。腿 A 的库存行也记在 criterion='J1' 下（run_recal64 的口径）。"""
    m = {}
    for r in csv.DictReader(io.open(TAU_CSV, encoding='utf-8')):
        if r['criterion'] != 'J1' or r['tau_star'] in ('', 'NONE'):
            continue
        m[(r['template'], r['statistic'])] = float(r['tau_star'])
    return m


def _contract_row(task, why):
    """读 field_contract.csv：该题参照件实际报出的键。缺文件/缺行一律响亮停下。"""
    if not _CONTRACT:
        if not os.path.exists(CONTRACT_CSV):
            raise SystemExit('缺 %s ⇒ 先跑 build_field_contract.py。'
                             '用全局 FIELDS 顶替会把排队字段索要进库存题（%s 的 %s）'
                             % (CONTRACT_CSV, why, task['task_id']))
        for r in csv.DictReader(io.open(CONTRACT_CSV, encoding='utf-8')):
            _CONTRACT[r['task_id']] = r['keys'].split()
    keys = _CONTRACT.get(task['task_id'])
    if not keys:
        raise SystemExit('field_contract.csv 里没有 %s 这一行（%s）⇒ 停下补契约，不猜'
                         % (task['task_id'], why))
    return set(keys)


def contract_fields(task, why='grade', taus=None):
    """返回 (required, optional)，两者都从**该题参照件的键 × 该题有 τ\\* 的观测量**推出来。

    required = 本仪器在这一格真能比的观测量（τ* 表里的 statistic ∩ 参照件报了它）+ 参照件报了的口径字段；
    optional = 参照件还报了、但恒等式判据才用得上的字段（prompt 里写成"建议"，判分不硬要）。
    刻意不用 `output_contract` 当依据：那是题面自带的窄清单（mm1 只有 W、L），
    照它判会把"没报 busy_frac"当成合规，而腿 A 明明对 busy_frac 标了 τ*。

    ⚠ 两处 2026-10-17 补的闸（外部审计 F-6）：
    ① `trig_*` 是**仪器内部**的机制计数器，参照件现在也会报它们 ⇒ 必须显式减掉，
       否则哪天有人把 `keys` 直接铺进 prompt，就是让被测模型自报我的计数器。
    ② 凡标了 τ* 却**不在**该题参照件键集里的统计量，一律响亮停下。原来这里只 `s in keys` 过滤，
       等于"标定表多写一行就静默少比一个观测量"——§17 那次"向库存题索要 W/L"的**反向**同族错。
    """
    taus = taus if taus is not None else tau_map()
    keys = _contract_row(task, why)
    instr = keys & INSTRUMENT_KEYS
    unlisted = sorted(k for k in keys if k.startswith('trig_')) 
    if set(unlisted) - INSTRUMENT_KEYS:
        raise SystemExit('%s 的契约里出现清单外的仪器键 %s ⇒ 内核加了新计数器，'
                         '要么补进 INSTRUMENT_KEYS，要么它就不该被参照件报出'
                         % (task['task_id'], sorted(set(unlisted) - INSTRUMENT_KEYS)))
    orphan = sorted(s for (tpl, s) in taus if tpl == task['template'] and s not in keys)
    assert not orphan, ('τ* 表给 %s 模板的 %s 标了阈值，但该题参照件不报它 ⇒ 这格永远不可比；'
                        '要么补标定（重跑 build_tables_v2），要么删该 τ* 行，不许静默丢弃'
                        % (task['template'], orphan))
    cmp_able = sorted(s for (tpl, s) in taus if tpl == task['template'] and s in keys)
    assert cmp_able, ('%s 这一格没有任何"参照件报了、且标了 τ* 的"观测量 ⇒ 判分出口对它是瞎的'
                      % task['task_id'])
    required = sorted((set(cmp_able) | (keys & set(META))) - INSTRUMENT_KEYS)
    want_extra = set(IDENT_FIELDS) | {k for k in keys if k.startswith('per_seed_')}
    optional = sorted((keys - set(required) - instr) & want_extra)
    return required, optional


def required_fields(task, why='grade', taus=None):
    return contract_fields(task, why, taus)[0]



def per_observable(obs, task, taus):
    """两条出口合并后的逐观测量读数：{o: {'rel','truth','est','tau','fire'}}，只留有 τ* 又有 rel 的。"""
    out = {}
    merged = {}
    for o, d in (C.j1_analytic(obs, task, tau=None).get('per_obs') or {}).items():
        merged[o] = d
    for o, d in (j1_inv(obs, task) or {}).items():
        assert o not in merged, '同一观测量被两条出口都认领：%s ⇒ 两个分母会打架，停下' % o
        merged[o] = d
    for o, d in merged.items():
        rel = d.get('rel')
        tau = taus.get((task['template'], o))
        if rel is None or tau is None:
            continue
        out[o] = dict(rel=rel, truth=d.get('truth'), est=d.get('est'), tau=tau,
                      fire=bool(rel > tau))
    return out


def cells(obs, task, taus):
    """给人看的行 + (一致数, 总数)。总数=0 意味着"这一件在本仪器下不可比"，不能当失败也不能当通过。

    ⚠ 2026-10-18 加了"口径违规"行（第四轮 R4-4），**同日又拆过一次**：原先一句
    "`J0a/J0c/J2a/J3a` 四条同时 NA" 是把**两个字段混在一起**说的，夸大了失声面。
    实际读法（逐条回 `criteria.py` 点过）：`runtime_units` 只关掉 **J0a/J0e**，
    `time_unit` 只关掉 **J0c/J2/J3**。现在按字段各印一行。
    这里仍然只**印**，不改 `n_in/n_tot`（免得把"看不见"偷换成"报警"）；
    逐件可比率里怎么处置它 = "不可比 + 计一次违规"，由 `analyze_legB.py` 分字段落列。
    """
    per = per_observable(obs, task, taus)
    rows, n_in = [], 0
    # 失声清单要按**字段↔判据**的实际读法拆成两条，不许再并成一句"四条同时失声"（2026-10-18 复算）：
    #   `runtime_units`  →  J0a / J0e（`criteria.py:290-291` 是全仓唯一读这个字段的地方）
    #   `time_unit`      →  J0c / J2 / J3（`criteria.py:291 htu`、`declared_unit_hours()` :404 及其调用者）
    # 权威参照件 `artifacts/*__REF.py` 写的是 `runtime_units='hours'`（单位名）⇒ 两条都不该点火；
    # 注意别拿 `calib_ref/` 那代（写的是计数）当参照，它不是现行出口（见任务 #42）。
    for fld, legs in (('runtime_units', 'J0a/J0e'), ('time_unit', 'J0c/J2/J3')):
        v = obs.get(fld)
        if v is not None and C._unit_hours_strict(v) is None:
            rows.append('口径违规(%s=%r 在词表外) ⇒ %s 失声（**不是合格，是看不见**）' % (fld, v, legs))
    for o, d in sorted(per.items()):
        n_in += (not d['fire'])
        rows.append('%s 报=%.4f 真=%.4f rel=%.1f%% τ*=%.3f %s' % (
            o, d['est'] if d['est'] is not None else float('nan'),
            d['truth'], 100 * d['rel'], d['tau'], '报警' if d['fire'] else '一致'))
    return rows, n_in, len(per)
