"""判分口径 J1-J6 的实现 + 参照件标定引擎（Step 2）。

预注册纪律（写死在本文件顶部，之后不许改）：
  * 阈值/假阳率只能在**已知正确的参照件**上标定；**现行权威出口 = `bench_v1/artifacts/*__REF.py`（64 题，
    `run_p0_crosscheck.py:24 ART` 与 `legB_grade.py:29 ART_DIR` 都指它；`runtime_units='hours'` 是单位名）**。
    `bench_v1/calib_ref/*__REF.py`（38 题）是 **Step 2 的 v1 历史出口**，它把 `runtime_units` 写成
    `seeds*horizon`（计数），与现行口径不同 ⇒ **不要拿它当参照去验 J0**（10-18 晚我就这么探错了一次，
    当场得出"stage1 表不可复现"的假警报；权威与出口要写在这里，别只写在注释里）；
  * 标定完成后不得再看变异工件结果回头改 τ；改了必须进"偏离记录"；
  * 禁止把错型标签 / mutants.jsonl 的任何字段当 J5 的签名输入。

口径清单：
  J1 解析对账   ：观测量估计值 vs task['truth_print']，|相对偏差| > τ(模板 × 观测量)。
  J2 守恒不变量 ：J2a Little L=?_eff*W；J2b 流量守恒 arr=dep+blk(+队内残留)；J2c 忙度<=1。
                 （J2d sum_wait=sum_dep-sum_arr 需要原始时刻和，当前契约没有 -> INTERFACE_GAPS.md）
  J3 定律配对   ：J3a PASTA 退化实现（时间平均忙度 vs 事件计数推算的占用率）；
                 J3b PASTA 队长分布版（卡方 + KS），需要到达时刻/时间平均的队长直方图，当前契约没有。
  J4 扰动响应   ：按题面角色改参数再跑，方向违反且超出噪声裕度 m 才报警。
  J5 结构签名   ：纯静态 AST 提取机制签名；与真值/标签无关。
  J6 LLM 裁判   ：只给 prompt 模板与调用接口，不发生任何网络调用（待腿B）。

统计口径（写死）：
  * 均值的 95% CI 用批均值法（MES）：跨种子批，t 系数按 df=种子数-1 查表；
  * 比率（假阳率）的 CI 用 Wilson (z=1.96)；
  * 试验单元有两级：task 级（n=模板题数，最多 8）与 batch10 级（n=题数 x floor(R/10)）。

单位约定（重要，必须在论文里写清）：
  参照实现 pilot_c6/pilot.py::run_once 的时间单位是**小时**，其 L 已在"先按事件前的 N 积分、
  再改状态"的修复后正确；它的**服务时长是在顾客被选入服务的那一刻才抽取**
  （d = rng.expovariate(mu) 在 serve() 开头、yield env.timeout(d) 之前）。
  这是"实现约定"不是定理：它使 LCFS/SIRO 的 L 与 FCFS 路径恒等（预注册 §9 第 3 条记的同一件事）。
  因此本参照集只能标定"估计噪声"，不能用来标定次序类错型的可检性。
"""
import os
import sys
import json
import math
import ast
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))          # .../bench_v1
ROOT = os.path.abspath(os.path.join(HERE, '..'))           # .../论文Q
TASKS_JSONL = os.path.join(HERE, 'tasks.jsonl')
CALIB_DIR = os.path.join(HERE, 'calib_ref')
PY = sys.executable

# ------------------------------------------------------------------ 固定常量
CRITERION_IDS = ('J1', 'J2', 'J3', 'J4', 'J5', 'J6')
OBSERVABLES = ('W', 'L', 'p_loss', 'busy_frac', 'p_wait')
TAU_GRID = (0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.20)
WILSON_CONF_Z = 1.96
WILSON_TARGET_UPPER = 0.05          # 标定目标：假阳率的 Wilson 95% 上界 <= 5%
BATCH_R = 10                        # batch 级试验单元的批大小（种子）
UNITS_PER_SEC = 19200.0             # 实测：horizon=8000->0.416s, 80000->4.175s（线性）
PROC_STARTUP_SEC = 0.55             # 实测近似：python 启动 + import simpy
# 判定出口在这里只核对**口径自述**两件。逐题该报哪些观测量，是 `gen_legB.required_fields()`
# 按 field_contract.csv（= 该题参照件的实际输出键）决定的，不在这里硬编码。
# ⚠ 这里原先是 ('W','L','p_loss','p_wait','busy_frac','runtime_units','seeds_used')：
#   那是把排队模板的词汇表当成全体工件契约。实测后果——eoq/newsvendor 的参照件只报 7/8 个键
#   （`build_field_contract.py` 计数），于是被判分端一律记成
#   note='missing:W,L,p_loss,p_wait,busy_frac'。腿 A 的脚本全部按 `obs is None` 分支、没人读这句 note，
#   所以既有 τ*/FP/主矩阵数字不受影响；但这是个静默陷阱：
#   将来任何"note 必须为 ok"的门一上，就当场吃掉 2/9 个模板。
META_REQUIRED_KEYS = ('runtime_units', 'seeds_used')
TEMPLATES_READY = ('mm1', 'mmc', 'mm1K', 'mmcK', 'md1')

# 模板 -> 该模板可跑的角色扰动（J4）
PERTURBATIONS = {
    'mm1':   ('lam_up', 'mu_up', 'c_up'),
    'mmc':   ('lam_up', 'mu_up', 'c_up'),
    'md1':   ('lam_up', 'mu_up', 'c_up'),
    'mm1K':  ('lam_up', 'mu_up', 'c_up', 'cap_down'),
    'mmcK':  ('lam_up', 'mu_up', 'c_up', 'cap_down'),
    'mh2':       ('lam_up', 'mu_up',),
    'jackson2':  ('lam_up', 'mu_up',),
    'newsvendor': (),
    'eoq':        (),
}
PERT_SCALE = {'lam_up': 1.15, 'mu_up': 1.25}
# 方向预期：'ge' => 扰动后观测量不减；'le' => 不增
PERT_EXPECT = {'lam_up': ('W', 'ge'), 'mu_up': ('W', 'le'),
               'c_up': ('W', 'le'), 'cap_down': ('p_loss', 'ge')}   # 容量收紧 => p_loss 不减


# ------------------------------------------------------------------ 统计工具
def tcoef(df):
    """双侧 95% 的 t 系数，df=自由度（查表 + 线性插值，本机无 scipy）。"""
    tab = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
           8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160,
           14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
           20: 2.086, 22: 2.074, 24: 2.064, 26: 2.056, 28: 2.048, 30: 2.042,
           35: 2.030, 40: 2.021, 45: 2.014, 50: 2.009, 60: 1.999, 70: 1.994,
           80: 1.990, 90: 1.987, 100: 1.984, 120: 1.980}
    if df <= 1:
        return float('nan')
    ks = sorted(tab)
    if df in tab:
        return tab[df]
    if df > ks[-1]:
        return 1.96
    lo = max(k for k in ks if k < df)
    hi = min(k for k in ks if k > df)
    w = (df - lo) / float(hi - lo)
    return tab[lo] * (1 - w) + tab[hi] * w


def mean_sd(vals):
    n = len(vals)
    if n == 0:
        return None, None
    m = sum(vals) / n
    if n < 2:
        return m, None
    v = sum((x - m) ** 2 for x in vals) / (n - 1)
    return m, math.sqrt(v)


def wilson(k, n, z=WILSON_CONF_Z):
    """二项比例的 Wilson 区间；n=0 返回 nan。"""
    if n <= 0:
        return (float('nan'), float('nan'))
    ph = k / float(n)
    d = 1.0 + z * z / n
    c = ph + z * z / (2.0 * n)
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4.0 * n * n))
    return ((c - half) / d, (c + half) / d)


def rel_dev(est, truth):
    if est is None or truth is None:
        return None
    try:
        if float(truth) == 0.0:
            return 0.0 if float(est) == 0.0 else float('inf')
        return abs(float(est) - float(truth)) / abs(float(truth))
    except (TypeError, ValueError):
        return None


def cost_seconds(seeds, horizon):
    """判定成本：seeds x horizon 个仿真时域单位，按实测线性 + 进程启动开销。"""
    return seeds * horizon / UNITS_PER_SEC + PROC_STARTUP_SEC


# ------------------------------------------------------------------ 题集与工件 IO
def load_tasks(path=TASKS_JSONL):
    out = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def ready_tasks(tasks=None):
    tasks = tasks if tasks is not None else load_tasks()
    return [t for t in tasks if (t.get('simpy_ref') or {}).get('ready')]


def ref_wrapper_path(task_id):
    return os.path.join(CALIB_DIR, '%s__REF.py' % task_id)


def parse_artifact_line(line):
    """工件 stdout 的最后一行 JSON -> obs dict。契约缺字段不报错，置 None（判据说不出就是缺字段）。"""
    txt = None
    for raw in reversed([x for x in line.splitlines() if x.strip()]):
        try:
            txt = json.loads(raw)
            break
        except ValueError:
            continue
    if txt is None:
        return None, 'no_json_line'
    obs = dict(txt)
    missing = [k for k in META_REQUIRED_KEYS if k not in obs]
    return obs, ('ok' if not missing else 'missing:' + ','.join(missing))


def run_artifact(path, seeds, horizon, pert='none', seed_start=1, timeout=3600):
    """以子进程跑参照件/工件，返回 (obs, wall_seconds, note)。

    ⚠ horizon 用 **整数样式**（`40000`）上线，不要 `str(40000.0)`='40000.0'：
      LLM 写的工件几乎都按 `int(args[i+1])` / `argparse type=int` 解析，'40000.0' 会
      ValueError 直接崩 —— 10-17 本地 8B 探针 20 道里 4 道就是这么死的，
      会被记成"模型不会写"。参照件（simcore 用 float()）两种写法都吃，
      已实测 `--horizon 40000` 与 `40000.0` 的输出 **31 个键逐位相同** ⇒ 换写法不影响腿 A 任何数。
    """
    cmd = [PY, path, '--seeds', str(int(seeds)), '--horizon', ('%g' % float(horizon)),
           '--seed-start', str(int(seed_start)), '--pert', pert]
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'          # 子进程 stdout 一律 UTF-8，控制台 GBK 不参与
    t0 = __import__('time').time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding='utf-8', errors='replace', env=env)
    except Exception as ex:
        return None, __import__('time').time() - t0, 'EXC %s' % ex
    dt = __import__('time').time() - t0
    if p.returncode != 0:
        return None, dt, 'rc=%s %s' % (p.returncode, (p.stderr or '')[-400:])
    obs, note = parse_artifact_line(p.stdout or '')
    return obs, dt, note


# ------------------------------------------------------------------ J1 解析对账
def j1_analytic(obs, task, tau=None, taus=TAU_GRID):
    """观测量估计值 vs truth_print。tau=None 时给出全网格的点火向量。

    只对 o in truth_print 且工件确实报出该字段的观测量计分（字段缺失 = 判不了，不是判过）。
    返回 {'per_obs': {o: {'rel','truth','est','fired_at'/'fired'}}, 'fired': bool}
    """
    truth = task.get('truth_print') or {}
    contract = task.get('output_contract') or {}
    unit = contract.get('W', '分钟')
    per = {}
    for o in OBSERVABLES:
        has_truth = truth.get(o) is not None
        est = obs.get(o)
        if not has_truth and est is None:
            continue
        if not has_truth:
            per[o] = dict(rel=None, est=est, truth=None, status='no_truth(该题无此真值)')
            continue
        if est is None:
            per[o] = dict(rel=None, est=None, truth=truth[o],
                          status='field_missing' + ('(契约点名)' if o in contract else ''))
            continue
        if o == 'W' and unit.startswith('秒'):
            est = est / 60.0
        rel = rel_dev(est, truth[o])
        d = dict(rel=rel, est=est, truth=truth[o], status='ok')
        if tau is None:
            d['fired_at'] = {('%g' % t): (rel is not None and rel > t) for t in taus}
        else:
            d['fired'] = bool(rel is not None and rel > tau)
        per[o] = d
    fired = None
    if tau is not None:
        fired = any(bool(v.get('fired')) for v in per.values())
    return dict(criterion='J1', per_obs=per, fired=fired, tau=tau)


def _unit_hours_strict(u):
    """认单位；**认不出来就返回 None**（原来 `_unit_hours(x, default=1.0)` 会把生词当"小时"，
    于是工件写 `time_unit='fortnight'` 就白拿一个不换算的通过 —— 同一族"可撒谎的口子"）。"""
    return _unit_hours(u, None)


def j0_unit_anchor(obs, task, tau=None, taus=TAU_GRID, horizon=None):
    """**J0 自报口径自洽**（2026-10-18 加；同日第四轮复算后**降级过一次**，见本 docstring 末段）。

    要堵的东西：`J1` 对闭式真值那一路不吃工件自报的单位（单位取自题集契约），但
    **`J2/J3` 的换算吃**（`w_in_rate_units` / `per_hour_to_rate_unit` 都读 `obs['time_unit']`），
    所以"工件自己声明什么单位"是能挪的门柱。实测过代价（`UNIT_HEALING_EXPOSURE.md`）：
    **把单位钉死会在 14 件 `E28` 上造假阳**（`J2a` 由 1e-5 跳到 0.9833）
    ⇒ 正确修法不是去掉自愈，而是加**外部可导出量对自报量的牵制**。

    四条腿。**先说清它检的是什么**：检的是"工件自报的这几个字段之间是否彼此自洽"，
    **不是**"工件报的数是不是真的"。第四轮外部复算给的构造（把 `arr` 改成任意值、
    再按 `win=arr/(λ·h)`、`dep_rate=dep/win` 反算）能让 `J0a/J0b/J0c` 同时归零而 `J1` 也不响
    （`J0_ANCHOR_GATES.md` 的 `反算凑平` 那一行）——因为 `win` 也是工件自报的，是自由量。
    ⇒ 这一族只能靠 `J0e`（窗口取**调用参数**导出的范围，工件改不了调用参数）去堵。

      `J0a_arrival_lambda` —— 到达条数 `arr` 对 **题面** λ × 自报 `win` × h(自报 `runtime_units`)。
          单改 `runtime_units`（谎报但不同步改 `win`）⇒ 预测挪 60 倍而 `arr` 动不了 ⇒ 必响（实测 rel=58.9）；
          诚实换单位（`E28`：数值与声明一起换）两边同步 ⇒ 不响。
      `J0b_rate_flow` —— 纯内部：`dep_rate × win ≈ dep`。抓"率与窗口用了两套单位"这类自相矛盾。
          ⚠ 它只在**不同步**时接得住：四维同步（`win×60` + `dep_rate÷60` + 两个声明都改分钟）
          本来就是合法的"内部用分钟"写法，rel=1.2e-16，**该静默**。
      `J0c_rate_lambda` —— `dep_rate` 对 **题面** λ×(1−`p_loss`)，换算读自报 `time_unit`
          （= stage1 里原先写死 0.01 阈值的那条 `G6`，现在折进 J0 统一实现、统一标定）。
          ⚠ **与 `J0a` 不是两条独立信息**：无丢失且 `arr=dep` 时两者代数同值（实测 mm1-01 相对差 2.6e-14），
          有界题上也只差 0.12%（mm1K-01）⇒ 正文只许说"两条独立信息（计数-窗口、率-窗口）+ 一条题面锚"。
      `J0e_win_invocation` —— 自报 `win` 折成小时后必须落在 **调用参数** 允许的区间
          `[horizon×(1−W_WINDOW_MAX), horizon]`。`horizon` 是判分器自己传进去的调用参数，
          工件改不动 ⇒ 这一腿是真正的"改不掉"。
          ⚠ **不能写成恒等式 `win + warmup_units = horizon`**：`warmup_units` 是内核发的常量
          （`simcore.py:919` = `WARM_DEFAULT×horizon`），E26/E30/E28 实测不闭合
          （50000 / 30000 / 1.81e6 对 40000）⇒ 恒等式会一次在 34 件真良性件上造假阳。
          预热占比被合法错型改到离散值（0 / 0.25 / 0.5），所以判据只能是**区间**。

    字段不齐 ⇒ `rel=None` + status，**绝不算通过**；单位是词表外的生词也 ⇒ `rel=None` +
    `unknown_unit(...)`，并且**在返回值里留一条 `unit_violation` 痕迹**。
    留痕这条是 10-18 补的：NA 只表示"这几条判据失声"，不表示"工件没问题"——
    腿 B 里一个生词单位就一次关掉 `J0a/J0c/J2a/J3a` 四条，不留痕就等于让它是隐形的。
    """
    p = (task.get('params') or {})
    lam = p.get('lambda')
    res = {}
    arr, dep, win = obs.get('arr'), obs.get('dep'), obs.get('win')
    ru, tu = obs.get('runtime_units'), obs.get('time_unit')
    hru, htu = _unit_hours_strict(ru), _unit_hours_strict(tu)
    if lam and win is not None and arr is not None:
        if hru is None:
            res['J0a_arrival_lambda'] = dict(rel=None, est=arr, truth=None,
                                             status='unknown_unit(runtime_units=%r)' % (ru,))
        else:
            pred = float(lam) * win * hru
            rel = abs(arr - pred) / pred if pred else None
            res['J0a_arrival_lambda'] = dict(rel=rel, est=arr, paired=pred,
                                             status='ok' if rel is not None else 'zero_prediction')
    else:
        res['J0a_arrival_lambda'] = dict(rel=None, status='field_missing(lambda/arr/win)')
    if win is not None and dep is not None and obs.get('dep_rate') is not None:
        pred = obs['dep_rate'] * win
        rel = abs(dep - pred) / dep if dep else None
        res['J0b_rate_flow'] = dict(rel=rel, est=dep, paired=pred,
                                    status='ok' if rel is not None else 'zero_departures')
    else:
        res['J0b_rate_flow'] = dict(rel=None, status='field_missing(dep_rate/dep/win)')
    if lam and obs.get('dep_rate') is not None:
        if htu is None:
            res['J0c_rate_lambda'] = dict(rel=None, est=obs['dep_rate'], truth=None,
                                          status='unknown_unit(time_unit=%r)' % (tu,))
        elif obs.get('p_loss') is None:
            # 丢了 p_loss 就**不算**，不许当 0：有丢失的系统里 λ(1−0) 是错的预测，
            # 那会把"少报一个字段"的工件打成量纲错——仪器自己造假阳，是最贵的一类错。
            res['J0c_rate_lambda'] = dict(rel=None, est=obs['dep_rate'], truth=None,
                                          status='field_missing(p_loss)')
        else:
            pred = per_hour_to_rate_unit(obs, float(lam) * (1.0 - (obs.get('p_loss') or 0.0)))
            rel = abs(obs['dep_rate'] - pred) / pred if pred else None
            res['J0c_rate_lambda'] = dict(rel=rel, est=obs['dep_rate'], paired=pred,
                                          status='ok' if rel is not None else 'zero_prediction')
    else:
        res['J0c_rate_lambda'] = dict(rel=None, status='field_missing(lambda/dep_rate)')
    # ---- J0e：窗口长度对**调用参数**导出的区间（工件改不动调用参数，所以这腿才是真锚）----
    if win is None:
        res['J0e_win_invocation'] = dict(rel=None, status='field_missing(win)')
    elif not horizon:
        res['J0e_win_invocation'] = dict(rel=None, status='no_horizon(调用参数没传，不给默认)')
    elif hru is None:
        res['J0e_win_invocation'] = dict(rel=None, est=win, truth=None,
                                         status='unknown_unit(runtime_units=%r)' % (ru,))
    else:
        wh = win * hru                                   # 折成小时
        lo = float(horizon) * (1.0 - W_WINDOW_MAX)
        rel = max(0.0, wh - float(horizon), lo - wh) / float(horizon)
        res['J0e_win_invocation'] = dict(
            rel=rel, est=wh, paired=[lo, float(horizon)],
            status='ok' if rel <= 0.0 else 'out_of_invocation_range[%.0f,%.0f]h' % (lo, horizon))
    for d in res.values():
        if d.get('rel') is not None:
            d['fired_at'] = {('%g' % t): (d['rel'] > t) for t in taus}
            if tau is not None:
                d['fired'] = d['rel'] > tau
    fired = None
    if tau is not None:
        fired = any(bool(v.get('fired')) for v in res.values())
    # **口径违规留痕**：只要有任何一条腿因为"声明了词表外的单位"而失声，就记一次违规。
    # NA ≠ 安全：它只是这几条判据没法算，工件本身的问题一个字没被否证（第四轮 R4-4）。
    unit_violation = sorted({str(v.get('status')) for v in res.values()
                             if 'unknown_unit' in str(v.get('status') or '')})
    return dict(criterion='J0', per_stat=res, fired=fired, tau=tau,
                unit_violation=unit_violation)


# ------------------------------------------------------------------ 单位换算（判分第一道关）
# 词表按"合法写法"补齐（10-18 R4-4）：`ms`/`天`/`day`/`year` 这些原先不在词表里，
# 合法工件会被判成"词表外 ⇒ NA"，那是我这边把判据关掉，不是它报错。
_UNIT_HOURS = {'hour': 1.0, '小时': 1.0, 'h': 1.0,
               'minute': 1.0 / 60.0, '分钟': 1.0 / 60.0, 'min': 1.0 / 60.0,
               'millisecond': 1.0 / 3.6e6, '毫秒': 1.0 / 3.6e6, 'ms': 1.0 / 3.6e6,
               'second': 1.0 / 3600.0, '秒': 1.0 / 3600.0, 's': 1.0 / 3600.0,
               'day': 24.0, '天': 24.0, 'd': 24.0,
               'week': 168.0, '周': 168.0,
               'year': 8760.0, '年': 8760.0, 'y': 8760.0}
# 预热占用的合法最大值：错型目录里 `window` 只取 {0(E26), 0.25(参照), 0.5(E30)}。
# `J0e` 的区间下界由它定；以后加"预热更多"的错型必须同时改这里，否则会把合法件判成越界。
W_WINDOW_MAX = 0.5


def _unit_hours(u, default=None):
    if u is None:
        return default
    for k, v in _UNIT_HOURS.items():
        if str(u).strip().lower().startswith(k):
            return v
    return default


def w_in_rate_units(obs, task):
    """把工件报的 W（契约单位：分钟）换算到"事件率所用时间单位"的倒数。

    参照件与多数工件会把率写成**每小时**（time_unit='hour'），而 W 的契约单位是分钟，
    不换算就等于拿 60 倍的差去比 Little 定律 —— 这是 J2 最容易自己造出来的假阳。
    """
    W = obs.get('W')
    if W is None:
        return None
    wu = _unit_hours((task.get('output_contract') or {}).get('W', '分钟'), 1.0 / 60.0)
    tu = declared_unit_hours(obs)          # **没有可信声明 ⇒ None**，不许假定小时
    if tu is None:
        return None
    return W * (wu / tu)


def declared_unit_hours(obs):
    """工件自报口径的小时换算因子；**没声明或声明了词表外的单位 ⇒ None**。

    这里原来是 `_unit_hours(obs['time_unit'], 1.0)`——生词和缺字段都被当成"小时"，
    于是工件只要写一个 `time_unit='fortnight'` 就能把 J2a/J3a 的换算钉回对自己有利的口径
    （"单位自愈"最省事的一种）。认不出来就不算，让上层记 `unknown_unit` 而不是白拿一个通过。
    """
    return _unit_hours_strict(obs.get('time_unit'))


def per_hour_to_rate_unit(obs, x_per_hour):
    tu = declared_unit_hours(obs)
    return None if tu is None else x_per_hour * tu


# ------------------------------------------------------------------ J2 守恒不变量
def _na_reason(obs, need):
    """算不出来时把原因分清楚：**单位不可认 ≠ 字段缺失 ≠ 分母为 0**，三种 NA 在正文里的含义不同。

    这条不是装饰：把 `unknown_unit` 混进 `field_missing` 里，"工件撒谎声明单位"就会
    变成"这道题不可判"，而这正是 J0 要堵住的那一族。
    """
    if declared_unit_hours(obs) is None:
        return 'unknown_unit(time_unit=%r)' % (obs.get('time_unit'),)
    miss = [n for n, v in need if v is None]
    if miss:
        return 'field_missing(%s)' % '+'.join(miss)
    return 'zero_denominator'


def j2_conservation(obs, task, tau=None, taus=TAU_GRID):
    """守恒不变量。只用当前契约拿得到的聚合量；拿不到的记 status='field_missing'。

    J2a Little:  |L - lam_eff * W| / L     ，lam_eff = dep / win 由工件自报（dep_rate 字段）
    J2b 流量:    |arr - dep - blk| / arr   ，"队内残留"没有字段，只能当容差内的边界项
    J2c 忙度:    max(0, busy_frac - 1)
    J2d 和式:    |sum_wait - (sum_dep - sum_arr)| —— 需要原始时刻和，当前不可算
    """
    res = {}
    dep_rate = obs.get('dep_rate') if obs.get('dep_rate') is not None else obs.get('lam_eff')
    Wh = w_in_rate_units(obs, task)
    if None not in (obs.get('L'), Wh, dep_rate) and abs(obs['L']) > 1e-12:
        little = abs(obs['L'] - dep_rate * Wh) / abs(obs['L'])
        res['J2a_little'] = dict(rel=little, est=obs['L'], paired=dep_rate * Wh, status='ok')
    else:
        res['J2a_little'] = dict(rel=None, status=_na_reason(
            obs, [('W', Wh), ('dep_rate', dep_rate), ('L', obs.get('L'))]))
    arr, dep, blk = obs.get('arr'), obs.get('dep'), obs.get('blk')
    if None not in (arr, dep) and arr:
        flow = abs(arr - dep - (blk or 0)) / float(arr)
        res['J2b_flow'] = dict(rel=flow, status='ok')
    else:
        res['J2b_flow'] = dict(rel=None, status='field_missing(arr/dep/blk 计数)')
    if obs.get('busy_frac') is not None:
        res['J2c_busy'] = dict(rel=max(0.0, obs['busy_frac'] - 1.0), status='ok')
    else:
        res['J2c_busy'] = dict(rel=None, status='field_missing(busy_frac)')
    need = ('sum_wait', 'sum_dep_epoch', 'sum_arr_epoch')
    if all(obs.get(k) is not None for k in need):
        s = abs(obs['sum_wait'] - (obs['sum_dep_epoch'] - obs['sum_arr_epoch']))
        res['J2d_sum'] = dict(rel=s, status='ok')
    else:
        res['J2d_sum'] = dict(rel=None, status='field_missing(%s)' % '+'.join(need))
    for k, v in res.items():
        if tau is not None and v['rel'] is not None:
            v['fired'] = bool(v['rel'] > tau)
        elif tau is None and v['rel'] is not None:
            v['fired_at'] = {('%g' % t): (v['rel'] > t) for t in taus}
    fired = None
    if tau is not None:
        ok = [v for v in res.values() if v['rel'] is not None]
        fired = bool(ok) and any(v.get('fired') for v in ok)
    return dict(criterion='J2', per_stat=res, fired=fired, tau=tau)


# ------------------------------------------------------------------ J3 定律配对
def j3_pairing(obs, task, tau=None, taus=TAU_GRID):
    """J3a：时间平均忙度 vs 事件计数推算的占用率（PASTA 的退化配对，当前字段就能算）。

    对 G/G/c/K 平稳系统，服务台的时间平均占用率 = (离开率 x 平均服务时长) / c。
    两个估计量来自同一次运行的**不同样本路径**（时间积分 vs 事件计数），
    所以差得远就说明工件的统计口径不一致，而不需要任何解析真值。
    J3b：到达时刻看到的队长分布 vs 时间平均队长分布（卡方 + KS）——需要直方图字段。
    """
    p = (task.get('simpy_ref') or {}).get('kwargs') or task.get('params') or {}
    mu = p.get('mu')
    c = float(p.get('c', 1) or 1)
    res = {}
    dep_rate = obs.get('dep_rate') if obs.get('dep_rate') is not None else obs.get('lam_eff')
    tu = declared_unit_hours(obs)          # 与 J2a 同一口径：**认不出来就不算，不假定小时**
    # ⚠ 口径修正（2026-10-17，实测出来的，不是想当然）：
    #    dep_rate/(c·mu) 是**每台平均利用率** E[min(N,c)]/c；
    #    而 mmcK 的 busy_frac 按题集真值口径是 **1−π0**（"至少一台在忙"的概率）。
    #    两者在 c=1 时重合，所以这个矛盾只在"多服务台 + 有限容量"上暴露：
    #    实测 mmcK-01 用 busy_frac 差 0.298、mmcK-06 差 1.267（=把正确件打成严重不合格），
    #    改用 busy_util 后同一题差 5.4e-4 / 2.9e-4，与 mm1K/mmc 的 3.3e-4/1.3e-4 同量级。
    #    所以 J3a 必须吃 busy_util；老工件没报这个字段时才退回 busy_frac，并在 note 里标出来。
    used = 'busy_util' if obs.get('busy_util') is not None else 'busy_frac'
    bval = obs.get(used)
    if None not in (bval, dep_rate, mu, tu) and bval:
        pred = dep_rate / (c * mu * tu)              # mu 是"每小时"，换成率所用的时间单位
        rel = abs(bval - pred) / bval
        res['J3a_util_pasta'] = dict(rel=rel, est=bval, paired=pred, status='ok',
                                     field=used,
                                     note='' if used == 'busy_util' else 'J3a退化:用了busy_frac')
    else:
        res['J3a_util_pasta'] = dict(rel=None, status=_na_reason(
            obs, [('dep_rate', dep_rate), (used, bval), ('mu', mu)]))
    res['J3b_pasta_qdist'] = _j3b(obs, task)
    for k, v in res.items():
        if v['rel'] is None:
            continue
        if tau is not None:
            v['fired'] = bool(v['rel'] > tau)
        else:
            v['fired_at'] = {('%g' % t): (v['rel'] > t) for t in taus}
    fired = None
    if tau is not None:
        ok = [v for v in res.values() if v['rel'] is not None]
        fired = bool(ok) and any(v.get('fired') for v in ok)
    return dict(criterion='J3', per_stat=res, fired=fired, tau=tau)


def _j3b(obs, task):
    """PASTA 队长分布版：卡方统计量（也报 KS），只吃工件自报的两张直方图。"""
    ht = obs.get('q_time_hist')
    ha = obs.get('q_arrival_hist')
    if not ht or not ha:
        return dict(rel=None, status='field_missing(q_time_hist/q_arrival_hist)', chi2=None, ks=None)
    return pasta_chi2(ht, ha)


def pasta_chi2(hist_time, hist_arrival):
    """两分布的卡方拟合优度（按期望频数>=5 合并尾部）+ KS 距离。

    返回 rel = KS 距离（当作两分布的"相对差"口径，便于与 TAU_GRID 共用），
    同时给 chi2 与 df、p 值（df>=1 的卡方上尾用 Wilson-Hilferty 近似，本机无 scipy）。
    """
    n_t = float(sum(hist_time.values()))
    n_a = float(sum(hist_arrival.values()))
    if n_t <= 0 or n_a <= 0:
        return dict(rel=None, status='empty_hist', chi2=None, ks=None)
    keys = sorted(set(hist_time) | set(hist_arrival))
    ft = [hist_time.get(k, 0) / n_t for k in keys]
    fa = [hist_arrival.get(k, 0) / n_a for k in keys]
    ks = max(abs(x - y) for x, y in zip(ft, fa))
    exp = [(a + b) / 2.0 * n_a for a, b in zip(ft, fa)]
    obs_ = [hist_arrival.get(k, 0) for k in keys]
    # 合并期望频数 < 5 的桶
    keep_o, keep_e = [], []
    for o, e in zip(obs_, exp):
        if e >= 5.0:
            keep_o.append(float(o))
            keep_e.append(e)
    if len(keep_e) < 2:
        return dict(rel=ks, status='too_few_bins', chi2=None, ks=ks, df=len(keep_e) - 1)
    chi2 = sum((o - e) ** 2 / e for o, e in zip(keep_o, keep_e))
    df = len(keep_e) - 1
    return dict(rel=ks, status='ok', chi2=chi2, ks=ks, df=df,
                p_value=chi2_sf_approx(chi2, df))


def chi2_sf_approx(x, df):
    """卡方上尾概率的 Wilson-Hilferty 正态近似（无 scipy）。"""
    if df <= 0 or x < 0:
        return float('nan')
    z = ((x / df) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * df))) / math.sqrt(2.0 / (9.0 * df))
    return 0.5 * math.erfc(z / math.sqrt(2.0))


# ------------------------------------------------------------------ J4 扰动响应
def j4_direction(base, pert, kind, margin=None, margins=TAU_GRID):
    """方向检查。base/pert 是两个配置各自的 obs（同 seeds、同 horizon）。

    报警条件 = 方向违反 **且** 超出噪声：噪声用两个独立估计的合并半宽
      se_diff = t * sqrt(se_base^2 + se_pert^2)（se 由工件报的 per_seed 数组算；没有就退回用裕度 m）
    margin 为 None 时返回全网格点火向量。
    """
    okey, sense = PERT_EXPECT[kind]
    b, q = base.get(okey), pert.get(okey)
    if b is None or q is None:
        return dict(criterion='J4', kind=kind, obs=okey, rel=None,
                    status='field_missing(%s)' % okey, fired=None)
    b, q = float(b), float(q)
    scale = max(abs(b), 1e-12)
    if sense == 'ge':                                  # 应当不减：q < b 才是违反
        viol = (b - q) / scale
    else:                                              # 应当不增：q > b 才是违反
        viol = (q - b) / scale
    out = dict(criterion='J4', kind=kind, obs=okey, base=b, pert=q,
               viol=viol, status='ok',
               se_diff=paired_se_diff(base, pert, okey))
    if margin is None:
        out['fired_at'] = {('%g' % m): (viol > m and _not_powered(out, m)) for m in margins}
        out['fired_powered_at'] = {('%g' % m): (viol > max(m, 2.0 * (out['se_diff'] or 0.0)))
                                   for m in margins}
    else:
        out['fired'] = bool(viol > margin)
        out['fired_powered'] = bool(viol > max(margin, 2.0 * (out['se_diff'] or 0.0)))
    return out


def _not_powered(d, m):
    se = d.get('se_diff')
    return True if not se else d['viol'] > max(m, 2.0 * se)


def paired_se_diff(a, b, key):
    """两个配置间差值的 95% 半宽（按独立处理，保守）。per-seed 数组缺失 -> None。"""
    va, vb = a.get('per_seed_%s' % key), b.get('per_seed_%s' % key)
    if not va or not vb or len(va) < 2 or len(vb) < 2:
        return None
    ma, sa = mean_sd(va)
    mb, sb = mean_sd(vb)
    t = tcoef(min(len(va), len(vb)) - 1)
    return t * math.sqrt(sa * sa / len(va) + sb * sb / len(vb)) / max(abs(ma), 1e-12)


# ------------------------------------------------------------------ J5 结构签名
RES_CLASSES = ('Resource', 'Store', 'FilterStore', 'PriorityResource',
               'Container', 'Signal', 'Event', 'Interrupt')
CAP_WORDS = ('cap', 'K', 'limit', 'maxsize', 'capacity', 'queue_limit')


def j5_signature(src):
    """静态提取机制签名。**只看源码**，不读真值、不读错型标签、不读 mutants.jsonl。"""
    sig = dict(resource=set(), svc_draw=set(), svc_dist=set(), capacity_check=set(),
               queue_pick=set(), warmup=set(), print_fields=set(),
               rng_streams=0, arr_process=set(), uses_timeout=False,
               area_integral=set(), n_def=0, flags=set())
    try:
        tree = ast.parse(src)
    except SyntaxError:
        sig['flags'].add('unparsable')
        return _sig_freeze(sig)
    lines = src.splitlines()
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    sig['n_def'] = len(funcs)
    for node in ast.walk(tree):
        # 资源类型
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            base = node.func.value
            if isinstance(base, ast.Name) and base.id == 'simpy' and node.func.attr in RES_CLASSES:
                sig['resource'].add(node.func.attr)
        # 随机流个数
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and re.match(r'^rng\w*$', t.id):
                    if _is_rng_call(node.value):
                        sig['rng_streams'] += 1
        # 抽样分布
        if isinstance(node, ast.Call):
            fn = node.func
            nm = getattr(fn, 'attr', None) or (getattr(fn, 'id', None) if isinstance(fn, ast.Name) else None)
            if nm in ('expovariate',):
                sig['svc_dist'].add('exp')
            elif nm in ('uniform', 'gauss', 'normalvariate', 'random'):
                sig['svc_dist'].add('other:' + nm)
            if nm == 'timeout':
                sig['uses_timeout'] = True
        # 取队首/队尾/随机/最短队
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            a = node.func.attr
            v = node.func.value
            name = getattr(v, 'id', '') if isinstance(v, ast.Name) else getattr(v, 'attr', '')
            if a == 'pop':
                has_arg = bool(node.args)
                if not has_arg:
                    sig['queue_pick'].add('pop_last(LCFS)')
                elif isinstance(node.args[0], ast.Constant) and node.args[0].value == 0:
                    sig['queue_pick'].add('pop_first(FCFS)')
                elif _contains_rng_call(node.args[0]):
                    sig['queue_pick'].add('pop_random(SIRO)')
                else:
                    sig['queue_pick'].add('pop_index(其他)')
            elif a == 'append' and isinstance(name, str) and re.search(r'(wait|queue|q|line)', name, re.I):
                sig['queue_pick'].add('append_queue')
            elif a == 'sort' or a == 'heapify':
                sig['queue_pick'].add('sorted/priority')
            elif a == 'min' and name:
                sig['queue_pick'].add('min_select')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'min':
            sig['queue_pick'].add('min_select')
        if isinstance(node, ast.Attribute) and node.attr in ('heappop', 'heappush'):
            sig['queue_pick'].add('heap')
        # 容量判断
        if isinstance(node, ast.Compare):
            for sub in [node.left] + node.comparators:
                if isinstance(sub, ast.Name) and sub.id in CAP_WORDS:
                    sig['capacity_check'].add('explicit_name')
                if isinstance(sub, ast.Attribute) and getattr(sub, 'attr', '') in CAP_WORDS:
                    sig['capacity_check'].add('explicit_name')
        if isinstance(node, ast.Attribute) and node.attr == 'capacity':
            sig['capacity_check'].add('resource.capacity')
        # 预热
        if isinstance(node, (ast.Name, ast.Attribute)):
            t = getattr(node, 'id', None) or getattr(node, 'attr', None)
            if t and re.search(r'warm|win_start|warmup', str(t), re.I):
                sig['warmup'].add('uses_warmup_var')
        # 到达过程
        if isinstance(node, ast.Assign) and _is_timeout_of(node.value):
            sig['arr_process'].add('timeout_expr')
    ps = [f for f in funcs if _scope_has_print(f)]
    if not ps and _scope_has_print(tree):
        ps = [tree]
    sig['print_fields'] = set(_printed_keys(ps))
    if not sig['resource']:
        sig['resource'].add('none_list_based')
    if 'uses_warmup_var' not in sig['warmup']:
        sig['warmup'].add('no_warmup_variable_seen')
    sig['svc_draw'] = _service_draw_site(tree)
    sig['area_integral'] = _area_order(tree)
    return _sig_freeze(sig)


def _is_rng_call(v):
    s = ast.dump(v)
    return 'Random' in s or 'expovariate' in s


def _contains_rng_call(node):
    s = ast.dump(node)
    return 'expovariate' in s or 'random' in s.lower()


def _is_timeout_of(v):
    return isinstance(v, ast.Call) and getattr(v.func, 'attr', None) == 'timeout'


PRINT_MARK = ('print', 'dumps', 'write')


def _scope_has_print(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            nm = getattr(n.func, 'attr', None) or getattr(n.func, 'id', None)
            if nm in PRINT_MARK:
                return True
    return False


def _keys_in(node):
    """dict 字面量的键 + dict(...) 的关键字参数名。"""
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Dict):
            for k in n.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    out.add(k.value)
        if isinstance(n, ast.Call):
            fname = getattr(n.func, 'id', None) or getattr(n.func, 'attr', None)
            if fname == 'dict':
                out.update(kw.arg for kw in n.keywords if kw.arg)
    return out


def _printed_keys(scopes):
    """只在"含 print/dumps/write 的作用域"里收字段名，否则会把元数据字典也当打印字段。"""
    out = set()
    for s in scopes:
        out |= _keys_in(s)
    return out


SVC_ARG_PAT = re.compile(r'^(mu|srv|svc|serv|rate_?s|mean_?s|s_?mean|service)', re.I)
ARR_ARG_PAT = re.compile(r'^(lam|lambda|arr|inter|rate_?a|demand)', re.I)


def _arg_names(call):
    out = []
    for arg in list(call.args) + [kw.value for kw in call.keywords]:
        for n in ast.walk(arg):
            nm = getattr(n, 'id', None) or getattr(n, 'attr', None)
            if nm:
                out.append(str(nm))
    return out


def _fn_span(f):
    ends = [n.lineno for n in ast.walk(f) if hasattr(n, 'lineno')]
    return f.lineno, max(ends or [f.lineno])


def _fn_role(f):
    """函数角色：服务过程 vs 到达过程（纯结构标记，不看函数名）。"""
    code = ast.dump(f)
    enq = any(isinstance(n, ast.Call) and getattr(n.func, 'attr', '') == 'append'
              for n in ast.walk(f))
    rel = bool(re.search(r"(in_svc|busy|release|free)", code)) or any(
        isinstance(n, ast.AugAssign) and isinstance(n.op, ast.Sub) for n in ast.walk(f))
    if enq and not rel:
        return 'arrival'
    if rel:
        return 'server'
    return 'other'


def _service_draw_site(tree):
    """服务时长抽样点：在服务过程里抽（=服务开始时刻）还是在到达过程里抽（=挂载到顾客身上）。

    这正是本项目最要紧的一条机制差异：pilot.py 是前者（使 LCFS 的 L 与 FCFS 路径恒等），
    pilot4.py 是后者（只期望相等）。抽不出来就老实标 unknown。
    """
    sites = set()
    for f in (n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
        role = _fn_role(f)
        for node in ast.walk(f):
            if not isinstance(node, ast.Call):
                continue
            nm = getattr(node.func, 'attr', None) or getattr(node.func, 'id', None)
            if nm not in ('expovariate', 'uniform', 'normalvariate', 'gauss'):
                continue
            an = _arg_names(node)
            is_svc = any(SVC_ARG_PAT.match(x) for x in an)
            is_arr = any(ARR_ARG_PAT.match(x) for x in an)
            if is_svc and not is_arr:
                sites.add({'server': 'svc_draw@service_start',
                           'arrival': 'svc_draw@arrival_epoch',
                           'other': 'svc_draw@role_unknown'}[role])
            elif not is_svc and not is_arr:
                sites.add('svc_draw@arg_unnamed(role=%s)' % role)
    return sites or {'no_service_draw_identified'}


def _names_include(node, pats):
    """赋值目标里是否点到某个变量名（Name.id 或 Attribute.attr）；不用 ast.dump 免得 'N' 命中 'Name'。"""
    for n in ast.walk(node):
        nm = getattr(n, 'id', None) or getattr(n, 'attr', None)
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            nm = n.value                        # S['N'] 这种字典状态写法
        if nm and any(re.match(p, str(nm)) for p in pats):
            return True
    return False


def _area_order(tree):
    """时间平均 L 的面积积分与状态改写谁在前（pilot 的 bug 就是这一条）。"""
    out = set()
    for f in (n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
        integ = [n.lineno for n in ast.walk(f) if isinstance(n, ast.Call) and
                 (getattr(n.func, 'id', '') in ('integ',) or getattr(n.func, 'attr', '') in ('integ',))]
        nmut = []
        for node in ast.walk(f):
            if isinstance(node, (ast.AugAssign, ast.Assign)):
                tgts = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(_names_include(t, (r'^N$', r'^N[_\[]', r'^n_in')) for t in tgts):
                    nmut.append(node.lineno)
        if integ and nmut:
            out.add('integrate_before_state_change' if min(nmut) > min(integ) else 'state_change_before_integrate')
    return out or {'no_area_integration_seen'}


def _sig_freeze(sig):
    return {k: (sorted(v) if isinstance(v, set) else v) for k, v in sig.items()}


# J5 差异的可解释性：这些字段由**题面参数**决定，不同就是"可解释"
EXPLAINABLE_BY_PARAM = {'capacity_check', 'svc_dist', 'print_fields', 'svc_draw'}


def j5_compare(sig_a, sig_b, task_a=None, task_b=None):
    """两个签名的逐字段差异。返回 (diff_fields, unexplained_fields)。

    局限（必须在正文写）：签名是**语法**的，不是**语义**的——
      pop(0) 与 waiting[:1]+remove、for/while 两种写法，会被判成不同；
      所以 J5 报的是"写法不同"，不是"行为不同"，M13（无害冗余状态）天然是它的误报源。
    """
    diff, unexp = [], []
    for k in sorted(set(sig_a) | set(sig_b)):
        va, vb = sig_a.get(k), sig_b.get(k)
        if va != vb:
            diff.append(k)
            if k not in EXPLAINABLE_BY_PARAM:
                unexp.append(k)
    return diff, unexp


# ------------------------------------------------------------------ J6 LLM 裁判
J6_STATUS = 'stub_no_network'      # 待腿B：本节任何函数都不发网络请求


def judge_prompt(artifact_src, task, criteria_results=None):
    """J6 的 prompt 模板（只造文本，不调用）。返回 (system, user) 两段纯字符串。"""
    contract = task.get('output_contract') or {}
    fields = ', '.join('%s(%s)' % (k, v) for k, v in sorted(contract.items()))
    obs = []
    for o, v in sorted((task.get('truth_print') or {}).items()):
        obs.append('%s=%s' % (o, v))
    sys_txt = (
        '你是离散事件仿真代码的审查员。只判断"这段程序是否按题面把机制写对"，'
        '不要重写代码，不要给安慰分。输出严格 JSON：'
        '{"verdict":"pass|fail","error_type":"若无则为 none",'
        '"evidence_line":<行号>,"confidence":0~1,"reason":"<=60字"}。'
        '禁止依据：任何解析真值、任何外部标签。允许依据：题面文字与代码本身。')
    user_txt = (
        '题面：\n%s\n\n输出契约（字段与单位）：%s\n\n'
        '待审代码：\n%s\n'
        % ((task.get('desc_zh') or task.get('desc_en') or '').strip(), fields, artifact_src)
        + ('\n\n（可选）同一程序实际跑出的观测量，仅供你判断量级，不得当作已知答案：\n  '
           + ', '.join(obs) if obs else '')
    )
    if criteria_results:
        user_txt += '\n\n已有判据结果（供交叉参考，允许你不同意）：\n  ' + json.dumps(
            criteria_results, ensure_ascii=False, default=str)
    return dict(criterion='J6', status=J6_STATUS, system=sys_txt, user=user_txt,
                call=None)


def j6_call_disabled(*a, **k):
    raise RuntimeError('J6 不做任何网络调用（预注册：待腿B）')


# ------------------------------------------------------------------ 自检
def selftest():
    """不依赖标定结果的实现自检（含 J5 的"写法等价性"反例）。"""
    rows = []

    def chk(name, cond, detail=''):
        rows.append('[%s] %s %s' % ('PASS' if cond else 'FAIL', name, detail))

    task = dict(task_id='x', template='mm1',
                truth_print=dict(W=10.0, L=0.666667, p_loss=0.05),
                output_contract=dict(W='分钟', L='个', p_loss='概率0-1'),
                simpy_ref=dict(kwargs=dict(lam=4, mu=10, c=1)))
    obs = dict(W=10.05, L=0.6666, p_loss=None, p_wait=None, busy_frac=0.4,
               arr=1000.0, dep=999.0, blk=0.0, dep_rate=4.0, seeds_used=2,
               # 单位声明要**与数值自洽**（这条夹具 10-18 晚先错成"声明 minute 却给每小时率 4.0"，
               # 于是 J2a 报 rel=59.3 —— 那不是换算 bug，是夹具自己矛盾；权威参照件的写法是 hour）
               time_unit='hour', runtime_units='hour',
               per_seed_W=[10.0, 10.1], per_seed_L=[0.66, 0.67])
    r1 = j1_analytic(obs, task)
    chk('J1 小偏差在 1% 点火', r1['per_obs']['W']['rel'] < 0.01)
    chk('J1 缺字段=判不了', r1['per_obs']['p_loss']['status'].startswith('field_missing'))
    r2 = j2_conservation(obs, task, tau=0.02)
    # ⚠ 这一行原来写成 `r2[...]['rel'] < 0.01`，而 10-18 把"没有可信单位声明 ⇒ 不许假定小时"
    #    落进 `declared_unit_hours()` 之后，夹具里没声明单位的 obs 会让 `rel` 变成 None ⇒
    #    整个 selftest 在 TypeError 上崩，于是"判分器口径改过"这件事被藏了至少一天（红灯没亮，
    #    是灯座炸了）。现在：数值判 + 把新口径本身写成断言。
    j2a = r2['per_stat']['J2a_little']
    chk('J2a 可算（夹具已声明 time_unit）', j2a.get('rel') is not None and j2a['rel'] < 0.01,
        'rel=%s' % (j2a.get('rel'),))
    # **单位不变量**（今天真正该补的那条）：同一套物理量，率按小时报 vs 按分钟报，
    # J2a 的 rel 必须逐位相同。`Wh = W×(wu/tu)` 的设计意图就是这个——W 与率都换算到工件自报的
    # 那个时间单位上再相乘。这条断言是"88 件把率声明成 minute 的腿 B 工件会不会被 J2 冤枉"的判据；
    # 它要是塌了，就是拿 60 倍的差去比 Little 定律（本文件 :389 那句警告的字面版本）。
    o_h = dict(obs, time_unit='hour', dep_rate=4.0)
    o_m = dict(obs, time_unit='minute', dep_rate=4.0 / 60.0)
    rh = j2_conservation(o_h, task, tau=0.02)['per_stat']['J2a_little'].get('rel')
    rm = j2_conservation(o_m, task, tau=0.02)['per_stat']['J2a_little'].get('rel')
    chk('J2a 单位不变量（hour 声明 ≡ minute 声明）',
        rh is not None and rm is not None and abs(rh - rm) < 1e-9,
        'rel_hour=%s rel_minute=%s' % (rh, rm))
    j2n = j2_conservation(dict(obs, time_unit='fortnight'), task, tau=0.02)['per_stat']['J2a_little']
    chk('J2a 生词单位 ⇒ NA 不假定小时', j2n.get('rel') is None, str(j2n.get('status'))[:44])
    chk('J2d 缺字段如实标', 'field_missing' in r2['per_stat']['J2d_sum']['status'])
    r3 = j3_pairing(obs, task, tau=0.02)
    chk('J3a 可算', r3['per_stat']['J3a_util_pasta']['rel'] < 0.01)
    chk('J3b 缺直方图字段', r3['per_stat']['J3b_pasta_qdist']['status'].startswith('field_missing'))
    h = {0: 100, 1: 60, 2: 40}
    hh = {0: 102, 1: 58, 2: 40}
    chk('J3b 实现自检-同分布 KS 小', pasta_chi2(h, hh)['ks'] < 0.02)
    chk('J3b 实现自检-移位 KS 大', pasta_chi2(h, {0: 60, 1: 90, 2: 50})['ks'] > 0.1)
    base = dict(W=10.0, p_loss=0.05, per_seed_W=[10.0, 10.2], per_seed_p_loss=[0.05, 0.05])
    chk('J4 方向满足不报警', j4_direction(base, dict(base, W=11.0), 'lam_up', margin=0.01)['fired'] is False)
    chk('J4 方向违反且超裕度报警', j4_direction(base, dict(base, W=9.0), 'lam_up', margin=0.01)['fired'] is True)
    chk('J4 违反在噪声内不报警', j4_direction(base, dict(base, W=9.995), 'lam_up', margin=0.001)['fired_powered'] is False)
    # ⚠ 2026-10-18 改：这里原先是 `ref_wrapper_path('mm1-01')`（历史代 calib_ref）**并且带一个
    #    `else 'x=1'` 的静默兜底**——参照件一旦不在，J5 就拿 'x=1' 当载体照样"通过"，那是半个门禁
    #    （计数但不咬人）。现在换成现行权威出口 + 先断言载体存在。
    src_ref = open(os.path.join(HERE, 'artifacts', 'mm1-01__REF.py'),
                   encoding='utf-8').read()
    sig = j5_signature(src_ref)
    chk('J5 载体存在且能解析（artifacts 代）', 'unparsable' not in sig['flags'])
    eq_a = j5_signature('import simpy,random\nr=simpy.Resource(1)\n')
    eq_b = j5_signature('import simpy,random\nr=simpy.Resource(1)\n')
    chk('J5 同源码签名相等', eq_a == eq_b)
    lim_a = j5_signature('def s(w):\n    c=w.pop(0)\n')
    lim_b = j5_signature('def s(w):\n    c=w[0]\n    w.remove(c)\n')
    chk('J5 局限实测：等价写法被判不同', lim_a['queue_pick'] != lim_b['queue_pick'],
        '%s vs %s' % (lim_a['queue_pick'], lim_b['queue_pick']))
    chk('Wilson k=0/n=38 上界>5%', wilson(0, 38)[1] > 0.05, 'ub=%.4f' % wilson(0, 38)[1])
    chk('Wilson k=0/n=80 上界<=5%', wilson(0, 80)[1] <= 0.05, 'ub=%.4f' % wilson(0, 80)[1])
    chk('J6 无网络', judge_prompt('print(1)', task)['call'] is None)
    return rows


if __name__ == '__main__':
    # 中文行直接 print 到 GBK 控制台会在 '⇒' 上崩（本机老坑，今天第三次撞上），
    # 所以：全文落 UTF-8 文件，控制台只打 ASCII 摘要；**失败项数当退出码**（计数必须进退出码，
    # 否则调用方只能"看见红字"却看不见红）。
    rows = selftest()
    n_fail = sum(1 for r in rows if r.startswith('[FAIL]'))
    with open(os.path.join(HERE, 'CRITERIA_SELFTEST.md'), 'w', encoding='utf-8') as fh:
        fh.write('# criteria.py 实现自检（共 %d 项，FAIL %d）\n\n```\n%s\n```\n'
                 % (len(rows), n_fail, '\n'.join(rows)))
    print('items=%d FAIL=%d -> CRITERIA_SELFTEST.md' % (len(rows), n_fail))
    sys.exit(1 if n_fail else 0)
