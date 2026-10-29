"""bench_v1 统一仿真内核：9 个模板的"正确版" + 错型目录的显式分支。

写死的约定（与判分器共享接口一致，别改）：
- 时间基：λ、μ 都是"每小时"，horizon 也用小时；newsvendor 用"天"、eoq 用"年"。
- **服务时长在顾客到达该节点时就抽好并挂在顾客身上**（不是开始服务时才抽）。
  这是 P1 路径恒等的前提：否则"次序不改变 L/W"会变成实现的产物而不是定理的结论。
- **面积积分 integ() 必须在任何状态改变之前调用**。本项目旧代码把 integ() 放在
  N+=1 之后，L 系统性偏高约 0.1（修前 4.1326±0.0448、修后 4.0200±0.0450，闭式 4.0000）。
- 每个错型只碰**一个 hook**（ERRORS[etype] 只有一个键，结构上保证"单点"）。
- 主 RNG 流只用于到达间隔/服务时长/耐心；选人次、重复计数等辅助随机走 rng2，
  以保证 E01/E02/E03/E24/E29 这类"次序类/无害类"错型与 REF 共享同一条流（配对比较）。

工件文件只是薄壳 `simcore.main('<task_id>','<etype>')`，所以 REF 与变异件的源码
diff 恒等于 1 行；单点性由 ERRORS 的结构约束 + make_mutants 的 difflib 自查共同保证。
"""
import os
import sys
import json
import math
import random
import heapq
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(HERE, 'tasks.jsonl')

# ------------------------------------------------------------------ 内核常数
WARM_DEFAULT = 0.25        # 参照口径：丢前 25% 预热（与 pilot_c6 / bench.py 一致）
BATCH_N = 2                # E12：一次到达事件放进几人
TIMEVARY_AMP = 0.25        # E13：λ(t)=λ(1+amp·sin(2πt/24))
TIMEVARY_PERIOD = 24.0
JOCKEY_DT = 0.02           # E23：换队检查间隔（小时）
ABANDON_MEAN_MULT = 3.0    # E22：耐心 ~ Exp(均值 = 3·E[S])
DOUBLE_DEP_P = 0.05        # E27：5% 的离开事件被计两次
UNIT_SCALE = 60.0          # E28：λ、μ 同倍 ×60
UNIT_SCALE_DAYS = 365.0    # E35：年→日 同倍换算
T_DF19 = 2.093             # t_{0.975, df=19}（20 个种子，每种子一个估计）
EOQ_RATE_WINDOW_YEARS = 1.0  # E42：真实标本在"一年窗口里数订货次数"再反推需求率

HOOKS = ('discipline', 'arrivals', 'service', 'servers', 'cap', 'routing',
         'split', 'patience', 'time_base', 'rate_units', 'window', 'counting',
         'state', 'inv_opt', 'eoq_form',
         # 2026-10-18 补：腿 B 真实错型里注入谱整族没有的四类（见 COVERAGE_GAP.md (3)）
         'field_const', 'estimator', 'sched', 'solver')

# 每个错型 = 恰好一个 hook 的一次覆盖
ERRORS = {
    'E01': {'discipline': 'lcfs'},
    'E02': {'discipline': 'siro'},
    'E03': {'discipline': 'spt'},
    'E04': {'discipline': 'lcfs_pr'},
    'E25': {'discipline': 'lcfs_restart'},
    'E24': {'discipline': 'priority_class'},
    'E05': {'servers': 'minus1'},
    'E06': {'servers': 'frozen1'},
    'E07': {'rate_units': 'lam_mu_swap'},
    'E08': {'rate_units': 'service_per_minute'},
    'E09': {'arrivals': 'determ'},
    'E12': {'arrivals': 'batch'},
    'E13': {'arrivals': 'timevary'},
    'E10': {'service': 'invert_declared'},
    'E11': {'service': 'h2_to_exp'},
    'E14': {'cap': 'none'},
    'E15': {'cap': 'minus3'},
    'E16': {'cap': 'queue_as_system'},
    'E21': {'cap': 'no_baulk_action'},
    'E18': {'routing': 'drop2nd'},
    'E20': {'routing': 'stage_swap'},
    'E19': {'split': 'random'},
    'E23': {'split': 'jockey'},
    'E22': {'patience': 'abandon'},
    'E26': {'window': 'no_warm'},
    'E30': {'window': 'warm_half'},
    'E27': {'counting': 'double_dep'},
    'E28': {'time_base': 'scale60'},
    'E29': {'state': 'junk'},
    'E35': {'time_base': 'annual_to_daily'},
    'E31': {'inv_opt': 'cuco_swap'},
    'E32': {'inv_opt': 'no_salvage'},
    'E33': {'inv_opt': 'demand_determ'},
    'E34': {'inv_opt': 'mean_instead'},
    'E36': {'eoq_form': 'no_factor2'},
    'E37': {'eoq_form': 'swap_SH'},
    'E38': {'eoq_form': 'hold_full_qty'},
    # ---- 以下 5 类是 2026-10-18 由腿 B 的真实错型**反向**补进来的（COVERAGE_GAP.md (3)）----
    'E39': {'field_const': 'zero_W'},
    'E40': {'field_const': 'zero_busy'},
    'E41': {'sched': 'server_leak'},
    'E42': {'solver': 'rate_from_own_order_count'},
    'E43': {'estimator': 'little_backsolve'},
}

# 跑实验**之前**声明的目录：family / short / 适用模板 / expected / theory_ref。
# expected ∈ blind（理论上任何预算都查不出）/ weak（稀有触发或效应小，需大预算）
#           / detectable / benign（正确的做法，本该零报警）
# expected_by_tpl 覆盖个别模板的理论声明（在测量之前就改，理由写在 theory_ref）。
CATALOG = {
 'E01': dict(family='order', short='FCFS→LCFS(非预占)',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='blind',
   theory_ref='P1 恒等类，两条互不蕴含的来路（《定理层_P1P2P3_正式书写_2026-10-19.md》§1/§2）。'
              '引理 A=定长 ∧ 非预占 ⇒ 离去时刻多重集不变 ⇒ N(t) 逐位恒等（dL 实测 0，残量 3.1e-4）。'
              '引理 B=泊松 ∧ 指数 ⇒ 在服务者的残存需求仍是 Exp(μ) ⇒ N 是同一条生灭链 ⇒ 均值同律'
              '（残量 2.5e-3～5.0e-3，是抽样噪声不是恒等）。'
              '⚠【10-19 作废旧句】原写"work-conserving ∧ 不读服务时长 ⇒ 完成时刻集合与次序无关 ⇒ N(t) 路径同律"是错的：'
              '异质需求下不成立（两顾客同到、需求 1 与 10：FCFS 离去 {1,11}、LCFS {10,11}；V(t) 路径相同但 ∫N dt 是 12 对 21）。'
              '载体边界：mh2 是 H2 服务，两条引理都不覆盖 ⇒ 那 4 件只能记"幅度低于 τ*、未证恒等"；'
              'jackson2 由引理 C（引理 B + Burke 可逆性，前提=站间无容量、无分流）覆盖'),
 'E02': dict(family='order', short='FCFS→SIRO',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='blind',
   theory_ref='同 E01 的两条来路；SIRO 的选人走辅助 RNG，不污染到达/服务流。'
              '引理 A 的可核对推论：md1 上 E01/E02 的读数**逐位相同**（max rel 均 3.14e-4/3.26e-4）'
              '⇒ 残量只来自窗口边界、与被检规则无关。反证性证据：SIRO 在 mm1/mmc 上真发生非队首选取 15.8%/47.7%'),
 'E03': dict(family='order', short='FCFS→SPT(读服务时长)',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'mh2', 'jackson2'), expected='detectable',
   theory_ref='P2 边界 2×2：读服务时长 ∧ 服务有变异 ⇒ 可检（短的先走 ⇒ N(t) 变小 ⇒ W、L 下降）；M/D/1 上变异=0 ⇒ 退化恒等，故本类不套 md1'),
 'E04': dict(family='order', short='题目要非预占却写成预占式 LCFS',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='detectable',
   expected_by_tpl={'mm1': 'blind', 'mmc': 'blind', 'mm1K': 'blind', 'mmcK': 'blind',
                    'jackson2': 'blind'},
   theory_ref='预占破不破恒等，取决于两件事分开：① resume 保留已做工 ⇒ 工作量路径不变，但**破坏引理 A 的"非预占"前提**'
              '⇒ 定长载体可检；② 指数服务的无记忆 ⇒ 在服务的机器瞬时离去率仍是 μ ⇒ **引理 B 覆盖预占** ⇒ 均值不可检。'
              '带符号实测（`DIRECTION_SIGNED.md`，ΔW 相对同题 REF）：md1 +19.99% / +66.79%（变差）、'
              'mh2 −15.35% / −66.48%（变好）、mm1 −0.06% 与 mmc +0.06%'
              '（REF 自身 −0.11%/+0.02% ⇒ 落在噪声内，**方向不可定**）。'
              '三点与"符号 ∝ (1−cv²)"一致：cv²=0→+、cv²=1→0、cv²>1→−。'
              '⚠【10-19 作废旧公式】原写"差 = E[S]ρ(cv²−1)/(2(1−ρ))"**符号与实测相反**，'
              '且其中 LCFS-PR 的 M/G/1 均值式（E[T]=E[S]/(1−ρ)）我核不证 ⇒ 整条删除；'
              '只保留上面的带符号读数与"符号随变异方向翻转"这一实测规律，**量级未核**'),
 'E25': dict(family='order', short='预占后剩余服务时长不更新(重头再来)',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='detectable',
   theory_ref='中断丢弃已做工作 ⇒ 幻影工作量使 ρ_eff>ρ ⇒ W、L 同向上升（不依赖引理 A/B ⇒ 三种载体都该可检）。'
              '与 E04 的差只在 `simcore.py:585-586` 那两行（elapsed 归不归零）。带符号实测见 `DIRECTION_SIGNED.md`'),
 'E24': dict(family='priority', short='题面 FCFS 写成按服务时长二分类的严格优先级',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='detectable',
   expected_by_tpl={'md1': 'blind'},
   theory_ref='非预占优先级不改总工作路径但减小 N(t)（短类先走）⇒ W、L 下降；M/D/1 上两类时长相等 ⇒ 分类读不到位次 ⇒ 退化恒等'),
 'E05': dict(family='resource', short='服务台数少写 1',
   applies=('mmc', 'mmcK'), expected='detectable',
   theory_ref='Erlang-C Wq=C(a,c)/(cμ-λ)：c→c-1 使分母减小且 C(a,c) 上升 ⇒ W↑、L↑、busy↑'),
 'E06': dict(family='resource', short='服务台数写死为 1',
   applies=('mmc', 'mmcK'), expected='detectable',
   theory_ref='退化成 M/M/1：W=1/(μ-λ)；ρ=λ/(cμ)→λ/μ 可 ≥1 ⇒ 非稳态；J4 的"c↑⇒W↓"响应同时丢失'),
 'E07': dict(family='resource', short='λ 与 μ 互换',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='detectable',
   theory_ref='ρ=λ/μ→1/ρ>1 ⇒ 生灭链无上界、队长发散、W~H/2 随时域线性增长 ⇒ 小预算也查得出'),
 'E08': dict(family='resource', short='服务率时钟单位写错(单侧 60×)',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='detectable',
   theory_ref='只把 μ 一侧除 60 ⇒ ρ=λ/μ 放大 60 倍 ⇒ ρ≥1 非稳态。与 E28 的分界：ρ 是唯一的无量纲组合，同倍不动它(良性)、单侧必动它(建模错)'),
 'E09': dict(family='arrival_service_process', short='泊松到达写成定间隔',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='detectable',
   theory_ref='Kingman 近似 Wq≈λ( c_a²+ c_s² )E[S]/(2(1-ρ)) 中 c_a²:1→0 ⇒ W、L 下降；Poisson 增量独立性消失'),
 'E10': dict(family='arrival_service_process', short='服务分布与题面声明相反(指数↔定长)',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'jackson2'), expected='detectable',
   theory_ref='P-K：Lq=λ²E[S²]/(2(1-ρ))；E[S²]: det=1/μ² vs exp=2/μ² ⇒ 二阶矩差 2 倍。md1 上方向反过来（声明定长被写成指数 ⇒ W↑）'),
 'E11': dict(family='arrival_service_process', short='H2 两阶段混合指数写成指数(只改二阶矩)',
   applies=('mh2',), expected='detectable',
   theory_ref='P-K 只依赖 (E[S],E[S²])：均值不变、cv:1.5~3→1 ⇒ W 从 E[S](1+(1+cv²)ρ/(2(1-ρ))) 降到 E[S]/(1-ρ)，相对差=-(cv²-1)ρ/(2+(1+cv²)ρ)'),
 'E12': dict(family='arrival_service_process', short='批量到达(题面单到被写成 2 人一批)',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='detectable',
   theory_ref='λ_eff×2 ⇒ ρ×2 ⇒ W↑，多数题 ρ≥1 发散。题集 v1 没有声明批到达的题，"漏写批"这一方向无法实例化，故实现同一量级、符号相反的反向件'),
 'E13': dict(family='arrival_service_process', short='题面恒定泊松流被写成时变到达',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='weak',
   theory_ref='W(ρ)=ρ/(μ(1-ρ)) 对 ρ 凸 ⇒ 时间平均 λ 不变但 E[W] 上升(Jensen)；ρ(1+0.25)≥1 时周期过载 ⇒ 升为可检。题集 v1 无声明时变的题，故以注入方式实例化'),
 'E14': dict(family='capacity_blocking', short='系统容量上限漏写',
   applies=('mm1K', 'mmcK'), expected='weak',
   theory_ref='P3 **条件式**命题（2026-10-19 走 (a)：改句子不改标签；原句误标"P4"，P4 在同根估计量那格）。'
              '仅当被改写的约束只在**低概率状态 N=K** 生效（前提量 π_K→0）时：均值口径偏差 O(π_K·K/E[L]) 属二阶，'
              '计数口径 p_loss 的相对效应 Θ(1) 属一阶。'
              'π_K 由 M/M/c/K 的 Erlang 损失公式**从题面参数独立算出**（`P3_PRECONDITION_CHECK.py`，'
              '不许吃工件自报的 p_loss，否则退化成同源自洽）。'
              '本语料 16 组中**仅 3 组满足前提**（mmcK-06：ρ=0.2、π_K=0.0039）'
              '⇒ 实测均值偏 0.33%（<τ*=0.01，不可检）而 p_loss 偏 99.1～100%（可检）= 正面检验；'
              '其余 13 组 π_K≥1%、其中 10 组均值大幅点火（最大 rel(W)=3.215，mm1K-05 ρ=0.9、π_K=0.1602）'
              '⇒ **前提不成立，不作为本命题的检验**（不是反例）。标签维持 weak，50 件与头条四条不动'),
 'E15': dict(family='capacity_blocking', short='容量少 3(K→K-3)',
   applies=('mm1K', 'mmcK'), expected='weak',
   theory_ref='同 E14 的条件式写法。ρ<1 时 π_K∝ρ^K，K 减小使 p_loss 指数上升；均值二阶**只在 π_K→0 时成立**。'
              '⚠ 本族在 mmcK-06 上 K−3=1 < c=3 属退化参数 ⇒ π_K 不可算，该组按 NA 留名（不许静默丢行、也不许当 0）'),
 'E16': dict(family='capacity_blocking', short='把队列容量当成系统容量(少算在服务的 c 人)',
   applies=('mm1K', 'mmcK'), expected='weak',
   theory_ref='阻塞条件由"N≥K"写成"waiting≥K" ⇒ 有效容量 K→K+c，高态泄漏 π_{K+1..K+c}∝ρ^K；'
              '均值二阶同样**以 π_K→0 为前提**（本族 mmcK-06 的 π_K≈0 ⇒ 属满足前提的 3 组之一）。'
              '目录里的 E17(只有队列上限没有系统上限) 在本题集语义下与 E16 同一实现，已合并（见自检声明表）'),
 'E21': dict(family='capacity_blocking', short='满员流失(baulking)动作漏实现',
   applies=('mm1K', 'mmcK'), expected='weak',
   theory_ref='与 E14 行为相同、代码位不同（E14 改判定谓词、E21 删拒绝动作）⇒ P5 签名不可辨识的现成素材；'
              '均值/计数两档的可检性条件同 E14（**前提同样是 π_K→0**，不满足时均值也点火）'),
 'E18': dict(family='routing', short='两节点串联丢掉第二个节点',
   applies=('jackson2',), expected='detectable',
   theory_ref='Jackson 积式 W=W1+W2、L=L1+L2 ⇒ 丢一整项，相对缺口=W2/(W1+W2) 约 20-30%'),
 'E20': dict(family='routing', short='转移矩阵/工序顺序写反(先进 2 号台)',
   applies=('jackson2',), expected='blind',
   theory_ref='纯串联、转移概率 100% ⇒ 两节点都见泊松流 λ(Burke 定理) ⇒ W=W(λ,μ1)+W(λ,μ2) 是可交换和、L 同理 ⇒ 恒等。目录给的 detectable 在这一族不成立，声明阶段就改 blind'),
 'E19': dict(family='routing', short='共享队(等价 join-shortest)写成随机分流',
   applies=('mmc', 'mmcK'), expected='detectable',
   theory_ref='pooling 增益消失：分流后每支近似 M/M/1(λ/c,μ)，W=1/(μ-λ/c) > Erlang-C 的 W=1/μ+C(a,c)/(cμ-λ)'),
 'E23': dict(family='customer_behaviour', short='换队(jockeying)漏实现',
   applies=('mmc', 'mmcK'), expected='weak',
   theory_ref='以"分队+周期换队"近似共享队：work-conserving ∧ 不读服务时长 ⇒ 均值只差换队间隔的离散化残量 ⇒ 效应小、需大预算。题集 v1 无声明换队的题，故以"近似替代"方式实例化'),
 'E22': dict(family='customer_behaviour', short='中途放弃(reneging)漏实现',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='detectable',
   theory_ref='放弃销毁工作 ⇒ W↓、L↓；更硬的证据是计数不闭合 Σdep=Σarr-Σlost 而 lost 未上报 ⇒ J2 流量守恒直接点火。题集 v1 无声明耐心的题，故以注入方式实例化（同量级反号）'),
 'E26': dict(family='estimation', short='不去预热(warm_frac=0)',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='benign',
   theory_ref='初态空系统瞬态使前段 N(t) 偏低 ⇒ L、W 系统性低估 O(1/H)；属估计口径偏差而非建模错，短预算下必偏'),
 'E27': dict(family='estimation', short='离开事件重复计数',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='weak',
   theory_ref='L 用面积法 ∫N dt/H ⇒ 与计数无关；W 复制样本值 ⇒ 期望无偏只增方差 ⇒ J1 全盲；破坏的是 Σarr=Σdep+Σloss ⇒ 只有 J2 查得出'),
 'E28': dict(family='estimation', short='时间单位小时->分钟(率同除60、时域同乘60、输出口径同步换算)',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='benign',
   theory_ref='ρ=λ/μ 不变 ⇒ N(t) 的律不变 ⇒ L、busy、p_loss、p_wait 与 REF 同分布；输出口径也一起换算(W 同乘 60、time_unit 写 minute) ⇒ 按题集契约判 J1|W 实测 rel=1.1e-3 < τ*=0.01，**不报警**（读数出自 MUTANT_MATRIX_R10b.shard1.csv 的 mm1-02__E28；10-17 之前这一格写的是"工件没回乘 ⇒ J1-W 报警＝量纲假阳"，与矩阵读数矛盾，已按实测更正）。件仍属良性，但它是"单位自愈能把假阳藏起来"的标本：判分时把单位钉死 ⇒ J2a 由 1e-5 跳到 0.9833，见 UNIT_HEALING_EXPOSURE.md；堵法见 criteria.j0_unit_anchor'),
 'E29': dict(family='estimation', short='加了用不上的状态变量',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2', 'newsvendor'),
   expected='benign',
   theory_ref='冗余计数不消耗 RNG、不进入任何统计 ⇒ 与 REF 逐位相同 ⇒ J1/J2/J3/J4 零报警，只用来量 J5 逐字段比的误报'),
 'E30': dict(family='estimation', short='预热窗口写成"全部时间的一半"',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2', 'newsvendor'),
   expected='benign',
   theory_ref='warm_frac 0.25→0.5 只减少样本量（方差↑），不改稳态期望 ⇒ 与 REF 同分布、CI 更宽'),
 'E31': dict(family='inventory', short='报童 Cu/Co 用反',
   applies=('newsvendor',), expected='detectable',
   theory_ref='临界分位 cu/(cu+co) 与 co/(cu+co) 关于 0.5 镜像 ⇒ q 从 μ+z·sd 变到 μ-z·sd；利润随之下滑'),
 'E32': dict(family='inventory', short='报童忽略残值(salvage 当 0)',
   applies=('newsvendor',), expected='detectable',
   theory_ref='co=cost-salvage 变小 ⇒ 分位上升 ⇒ q↑；利润核算丢 salvage·E[(q-D)+] ⇒ q 与 exp_profit 同时偏离'),
 'E33': dict(family='inventory', short='需求过程写成定长(丢掉方差)',
   applies=('newsvendor',), expected='detectable',
   theory_ref='D≡μ_d ⇒ 利润=price·μ_d-cost·q+salvage·(q-μ_d)，缺了短缺/积压的损失项；q 来自分位数公式不受抽样影响 ⇒ "q 全对、利润偏"的部分可检格'),
 'E34': dict(family='inventory', short='用均值需求当订货量(忽略分位)',
   applies=('newsvendor',), expected='detectable',
   theory_ref='q=μ_d 而非 μ_d+z·sd ⇒ Δq=z·sd（cu>co 时 z>0 ⇒ 订货不足），期望利润按凸性损失'),
 'E35': dict(family='estimation', short='EOQ 时间单位同倍换算(年→日)',
   applies=('eoq',), expected='detectable',
   theory_ref='q=√(2DS/H)：D、H 同除 365 而 S 与时间无关 ⇒ q 不变（良性）；cost=√(2DSH) 变成"元/日"，工件按"元/年"口径上报 ⇒ 差 365 倍的量纲错（J1|cost 实测 rel≈0.997，可检）。与 E28 的分界就在输出口径：E28 把 W 与 time_unit 一起换 ⇒ 内部自洽、良性；E35 只换输入侧、cost 的口径没跟着换 ⇒ 可检（10-17 由 benign 改判为 detectable，理由见 mutants.jsonl 的 relabel_reason）'),
 'E36': dict(family='inventory', short='EOQ 根号内漏系数 2',
   applies=('eoq',), expected='detectable',
   theory_ref='q=√(DS/H) 使最优处"订货成本率=持有成本率"变成比值 √2 ⇒ q 偏 1/√2、cost 偏 +（√2-1）量级'),
 'E37': dict(family='inventory', short='EOQ 的 S 与 H 互换',
   applies=('eoq',), expected='detectable',
   theory_ref='q=√(2DH/S) ⇒ 倍数 = H/S（题集 H/S∈{0.04,0.01,0.2,0.05,...}）⇒ q 与 cost 同时偏离'),
 'E38': dict(family='inventory', short='持有成本按整批计(q·H 而非 q/2·H)',
   applies=('eoq',), expected='detectable',
   theory_ref='最优条件变 D/q·S=q·H ⇒ q 偏 √2 倍、成本项加倍 ⇒ q 与 cost 同时可检'),
 # ============ 2026-10-18：腿 B 真实错型反向补的 5 类（跑实验之前声明，见 COVERAGE_GAP.md (3)）============
 'E39': dict(family='estimation', short='等待时长根本没测，出口直接发常量 0（占位赋值没换掉）',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='detectable',
   theory_ref='真实标本：`legB/flash20261018/mh2-01__d3.py:84/:88` 的 `wait_area += 0.0`（该模式 12/192 件）。'
              '判据面：J1|W 的 rel=|0−W*|/W*≡1；J2a 的 paired=dep_rate·0=0 而 L>0 ⇒ rel≡1（预演 `_newop_smoke.md` (2) '
              '四个模板都是这两个数）。**不许据此说"两条独立证据"**——两者数值都是 1.0，按 R4-2 的相对差量级判据它们不是'
              '独立格；独立性的证据只能是"来源不同"（一条吃闭式真值、一条吃内部恒等式），要在主表里分开计数才成立'),
 'E40': dict(family='estimation', short='忙度累加变量从不置位，busy 一侧读数恒发 0',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='detectable',
   expected_by_tpl={'jackson2': 'blind', 'mmcK': 'blind', 'mm1K': 'blind'},
   theory_ref='真实标本：`legB/flash20261018/md1-01__d1.py:36` 的 `busy = 0` 之后再没被赋值 ⇒ busy_frac 精确 0。'
              '实现选择：砸的是**util 口径的源**（busy_util、busy_frac(当 busy_def=util/coincident)、busy_hw、per_seed_busy 全归 0），'
              'occupied 口径（1−π0，出自 nz 这条独立累加）保持真值。'
              '**【10-19 公开更正】** 本类第一次声明时我只把 occupied 口径猜在 mmcK 与 jackson2 上，'
              'R10c 实测把 mm1K-02/mm1K-05 判成 MISS ⇒ 声明错在题集侧：这两题的 `busy_def` 也是 `occupied`'
              '（truth_busy=0.4839/0.7558，与 ρ 不等，因阻塞使有效到达率低于 λ）。'
              '改声明后本类给出一条**14/14 无例外的分离律**：可检性完全由题集自己声明的口径决定——'
              'busy_def∈{util,coincident} 的 8 件全部 TP（J1|busy_frac rel≡1）；'
              'busy_def=occupied 的 4 件（mm1K-02/05、mmcK-03/06）全部检不出；'
              'busy_def=None（jackson2，无忙度真值）2 件全部检不出。'
              '两条仪器缺陷是这条律的成因，都要如实写：'
              '①`criteria.j3_pairing` 的门是 `... and bval`，bval=0.0 走 else ⇒ J3a 记 NA 而不是点火'
              '（预演四件的 J3a 全是 None）⇒ **"字段=0"与"字段缺失"在这条判据里不可区分**；'
              '②J2c 吃 busy_frac 但按定义 max(0,0−1)=0 永不点火（且已标 R0_VACUOUS_INTERNAL）⇒ 唯一能看到 '
              'busy_util 的腿也不响。⇒ 这不是"模型没犯错"，是**题集口径声明与判据覆盖面合起来把它藏了**。'),
 'E41': dict(family='scheduling', short='顾客离开后服务台槽位不置空（资源泄漏）⇒ 队列发散',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='detectable',
   theory_ref='真实标本：`legB/flash20261018/mh2-01__d3.py:51/:86` 的 `rem` 不递减（7/192 件，L 报 36002 vs 真值 0.509）。'
              '机制：每个服务台的**第一个**顾客离开后槽位仍被占住 ⇒ c 个槽位在预热窗口结束前就全被吃掉，'
              '此后 N(t) 以 λ 线性增长、L≈λH/2 随 H 发散（预演：mm1-01 的 L 在 H=2000→8000 时 5003→19911，'
              'mmc-03 9970→39918，都是 ×4=H 的倍数 ⇒ 确实是发散而不是稳态偏移）、J2b 流量守恒 |arr−dep−blk|/arr≡1。'
              'W：窗口内**一次离开都没有** ⇒ 出口发 null、J1|W 与 J2a 记 NA（不是"检不出"，是"判不了"；'
              '这条 NaN→null 的口径修正在 `_r6` 里，旧 346 件不产生 NaN 所以对本表惰性）。'
              '可检性不靠 W：J1|L=7.5e3、J1|busy_frac=1、J1|p_wait=1.5 三条各自点火。'
              '机制计数器 trig_leak = 被泄漏的槽位数（预演实测：mm1-01 每种子 1 台、mmc-03 每种子 6 台 = c），0 才算空转。'
              '与 E06(servers=frozen1) 的分界：E06 是**配置层**把服务台数写死为 1（一开跑就少 c−1 台，读数有界），'
              'E41 是**执行层**随时间把可用台数吃到 0 台（读数随 H 发散）'),
 'E42': dict(family='numerics', short='需求率从自己数出的订货次数反推，丢掉不满一轮的那一段',
   applies=('eoq',), expected='weak',
   theory_ref='真实标本：`legB/flash20261018/eoq-02__d1.py:60` 的 `est_q = D*(span/365.0)/orders`——闭式 q* 算对了，'
              '但出口报的是"仿真窗口里数出的次数"反推出来的 q̂。取一年窗口、orders=⌊D/q*⌋ ⇒ '
              'q̂/q*=√(⌊D/q*⌋/(D/q*))=√(1−frac/(D/q*)) ⇒ **偏差只由周期数是否落在整数上决定，与样本预算无关**。'
              '题集 6 题解析预算（D/q*, ⌊⌋, δq, δcost）：eoq-01 (4.4721,4,5.4258%,0.1555%)、eoq-02 (2.2361,2,5.4258%,0.1555%)、'
              'eoq-03 (10.0,10,**0,0**)、eoq-04 (5.0,5,**0,0**)、eoq-05 (10.0,10,**0,0**)、eoq-06 (5.0,5,**0,0**) ⇒ '
              '4/6 件偏差**精确为 0**（trig_lostcycle=0 ⇒ 按 INJECTION_IDLE 剔除，不进任何分母），'
              '活的 2 件里 q 偏 5.43% > τ*=0.01 可检、cost 偏 0.156% < τ* 不可检'
              '（EOQ 成本曲线在最优点右侧二次平坦：δcost≈δq²/2）⇒ 这是"一个工件两个观测量、判决相反"的现成格。'
              '⚠ 真实那 2 件的形态是 `while True` 永不退出（run=EXC/timeout），**根本进不了判据分母**，'
              '落链条的 CRASH/TIMEOUT 档；本算子建模的是"循环退出了并把未收敛值报出来"那一支，不是全部'),
 'E43': dict(family='estimation', short='W 不独立测量，用 Little 定律从自己报的 L 反推（自证式估计）',
   applies=('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'), expected='blind',
   theory_ref='真实标本：`legB/flash20261018/md1-01__d2.py:103` 的 `W = L/(win_dep/win_len)`（W_not_measured 38/192 件 = 19.8%）。'
              '取 W:=L/λ̂（λ̂=dep/win 正是工件自报的 dep_rate）⇒ J2a 的 paired=dep_rate·W=L，'
              'rel 被压到**出口 _r6 的 6 位小数舍入位**（≈1e-7 相对量级）而不是参照件那种 1.2e-5 的有限窗口余项——'
              '即 J2a 对这一类**逐格恒真**。J1|W 的偏差=|L̂/λ̂−W*|/W*，闭式真值满足 L*=λW* ⇒ 它与 J1|L 是**同一个估计量**'
              '（同量级，预演实测 mm1-01：J1|W=0.0192、J1|L=0.0216，差在 λ̂ 与 λ 的抽样差，不是两回事），'
              '量级 O(1/√R)，而 τ* 的标定恰恰要求 REF 的同量级噪声不点火 ⇒ 加大预算只会更不显著。'
              '这一类的错是**方法论的**（估计量与判据同源、独立性没了），不是数值的（W 仍是一致估计）⇒ 声明 blind。'
              '它是第二型不可检：E01/E02/E20 是**定理型**（物理恒等，任何实现都躲不掉），'
              'E43 是**自证型**（判据与被验对象共用同一估计量，换一套判据就能消掉）。'
              '真实腿 B 上这 38 件没有闭式真值可比 ⇒ J2a 是唯一可用的腿 ⇒ 彻底失声，这正是"仪器盲区"而不是"模型错"'),
}


# ------------------------------------------------------------------ 小工具
def t_ci(vals, tcoef=T_DF19):
    n = len(vals)
    m = sum(vals) / n
    if n < 2:
        return m, float('nan'), 0
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1))
    return m, tcoef * sd / math.sqrt(n), n - 1


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def norm_ppf(p):
    lo, hi = -12.0, 12.0
    for _ in range(120):
        mid = 0.5 * (lo + hi)
        if norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def h2_moments(mu, cv):
    """与题集真值同一参数化（mean=1/mu、CV=cv、p=1/(1+cv^2)）。"""
    p = 1.0 / (1.0 + cv * cv)
    q = 1.0 - p
    t = math.sqrt((cv * cv - 1.0) / (2.0 * p * q))
    return dict(p1=p, p2=q, r1=mu / (1.0 + t * q), r2=mu / (1.0 - t * p))


def load_tasks(path=TASKS_PATH):
    out = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


_CACHE = {}


def task_by_id():
    if 'tb' not in _CACHE:
        _CACHE['tb'] = {t['task_id']: t for t in load_tasks()}
    return _CACHE['tb']


def rho_of(task):
    p, tpl = task['params'], task['template']
    if tpl in ('newsvendor', 'eoq'):
        return 0.0
    if tpl == 'jackson2':
        return max(p['lambda'] / (60.0 / p['s1']), p['lambda'] / (60.0 / p['s2']))
    if tpl == 'mmcK':
        return p['lambda'] / (p['c'] * p['mu'])
    return p['lambda'] / p['mu']


# ------------------------------------------------------------------ 配置解析
def resolve(task, etype='REF'):
    if etype == 'REF':
        ov = {}
    else:
        ov = ERRORS[etype]
        assert len(ov) == 1, '错型必须只碰一个 hook: %s' % etype
    p, tpl = task['params'], task['template']
    cfg = dict(task_id=task['task_id'], template=tpl, etype=etype, hook=None,
               # busy_frac 的定义**由题集契约给**（bench.py 写真值时一并写进 busy_def），
               # 不再由内核看模板名去猜（外部审计 P-05：`occs if template=='mmcK' else busys`
               # 等于"按真值反选定义"，那条判据对参照件就永不可证伪）。
               busy_def=task.get('busy_def'),
               c=int(p.get('c', 1)),
               cap=int(p['K']) if tpl in ('mm1K', 'mmcK') else None,
               cv=p.get('cv'), params=p,
               nodes=2 if tpl == 'jackson2' else 1,
               lam=None, mus=None, cs=None, caps=None, svcs=None,
               discipline='fcfs', arrivals='poisson', service=None,
               servers='as_declared', cap_mode='system', routing='series',
               split='shared', patience='none', time_base=None, rate_units=None,
               window=WARM_DEFAULT, counting='normal', state='clean',
               inv_opt='fractile', eoq_form='correct',
               field_const=None, estimator='measured', sched='normal',
               solver='closed_form')
    if tpl in ('newsvendor', 'eoq'):
        cfg['lam'], cfg['mus'], cfg['cs'] = 0.0, [1.0], [1]
        cfg['svcs'] = ['det']
        cfg['cap_mode'] = 'none'
        hook, val = list(ov.items())[0] if ov else (None, None)
        cfg['hook'] = hook
        if hook == 'inv_opt':
            cfg['inv_opt'] = val
        elif hook == 'eoq_form':
            cfg['eoq_form'] = val
        elif hook == 'solver':
            cfg['solver'] = val
        elif hook == 'time_base':
            cfg['time_base'] = val
        elif hook == 'state':
            cfg['state'] = val
        elif hook == 'window':
            cfg['window'] = 0.0 if val == 'no_warm' else 0.5
        return cfg
    base_svc = {'md1': 'det', 'mh2': 'h2'}.get(tpl, 'exp')
    lam = float(p['lambda'])
    if tpl == 'jackson2':
        mus = [60.0 / float(p['s1']), 60.0 / float(p['s2'])]
    else:
        mus = [float(p['mu'])]
    hook, val = list(ov.items())[0] if ov else (None, None)
    cfg['hook'] = hook
    if hook == 'rate_units':
        cfg['rate_units'] = val
        if val == 'lam_mu_swap':
            lam, mus = mus[0], [lam] * len(mus)
        elif val == 'service_per_minute':
            mus = [m / UNIT_SCALE for m in mus]
    elif hook == 'time_base':
        cfg['time_base'] = val
        if val == 'scale60':
            # E28 原实现把 λ、μ 同倍 **乘** 60 而不动 horizon，
            # 于是物理上变成"同样长的一段时间里挤进 60 倍的顾客"：
            #   ① 事件量 60 倍 ⇒ 50 种子直接把内存吃光（14 件全崩），
            #   ② 报出的 W 差 60 倍 ⇒ 它根本不是良性件，是量纲错型。
            # 真正的"换时间单位"必须三处一起动：率除 60、时域乘 60、输出口径同步换算。
            lam = lam / UNIT_SCALE
            mus = [m / UNIT_SCALE for m in mus]
            cfg['t_scale'] = UNIT_SCALE          # 内部时间单位 = 小时/60 = 分钟
            cfg['w_out_factor'] = 1.0            # 内部已是分钟，契约也要分钟 ⇒ 不再乘 60
            cfg['internal_unit'] = 'minutes'
    elif hook == 'discipline':
        cfg['discipline'] = val
    elif hook == 'arrivals':
        cfg['arrivals'] = val
    elif hook == 'service':
        if val == 'invert_declared':
            base_svc = 'exp' if base_svc == 'det' else 'det'
        elif val == 'h2_to_exp':
            base_svc = 'exp'
    elif hook == 'servers':
        cfg['servers'] = val
    elif hook == 'cap':
        cfg['cap_mode'] = val
    elif hook == 'routing':
        cfg['routing'] = val
    elif hook == 'split':
        cfg['split'] = val
    elif hook == 'patience':
        cfg['patience'] = val
    elif hook == 'window':
        cfg['window'] = 0.0 if val == 'no_warm' else 0.5
    elif hook == 'counting':
        cfg['counting'] = val
    elif hook == 'state':
        cfg['state'] = val
    elif hook in ('field_const', 'estimator', 'sched'):
        cfg[hook] = val

    cs = [cfg['c']] * cfg['nodes']
    if hook == 'servers':
        if val == 'minus1':
            cs = [max(1, x - 1) for x in cs]
        elif val == 'frozen1':
            cs = [1] * len(cs)
    caps = [cfg['cap']] * cfg['nodes']
    if hook == 'cap' and val == 'minus3':
        caps = [max(1, k - 3) if k is not None else None for k in caps]
    cfg.update(lam=lam, mus=mus, cs=cs, caps=caps,
               svcs=[base_svc] * cfg['nodes'])
    return cfg


# ------------------------------------------------------------------ 排队内核
class Sim(object):
    def __init__(self, cfg, seed, horizon):
        self.cfg = cfg
        self.rng = random.Random(seed)
        self.rng2 = random.Random(seed * 7919 + 13)
        # CLI 传来的 horizon 一律按"小时"理解（题面约定）；
        # 换时间单位的良性件要把同一段时间用更细的单位表达，故乘 t_scale。
        self.H = float(horizon) * float(cfg.get('t_scale', 1.0))
        self.ws = cfg['window'] * self.H
        self.win = self.H - self.ws
        self.heap = []
        self._seq = 0
        self.t_now = 0.0
        self.last = 0.0
        self.N = 0
        self.gen = 0
        self.cid = 0
        self.A = dict(area=0.0, nz=0.0, busy=0.0, arr=0, arr_in=0, dep=0, blk=0, lost=0,
                      waits=0, soj=[], junk=0,
                      # 触发计数器（P-02/P-03）：恒等类的"没检出"必须有**机制真的跑起来**的证据，
                      # 否则那件是空转注入，既不能算盲区证实、也不能算漏检。四个量都只数事件、不改语义。
                      trig_nonhead=0,      # 选中的不是队首且队列>1 次（E01/E02/E03/E24 的落地证据）
                      trig_preempt=0,      # 真发生了预占（E04/E25）
                      trig_class0=0,       # priority_class 里被判为"剩余<1/μ"的人次（E24 是否真分了类）
                      trig_transfer=0,     # 顾客从节点 i 转到 i+1 的次数（网络题的活性）
                      trig_leak=0)         # E41：离开后没被置空的服务台槽位数（0=注入没落地）
        self.nodes = []
        for i in range(cfg['nodes']):
            self.nodes.append(dict(idx=i, c=cfg['cs'][i], mu=cfg['mus'][i],
                                   svc=cfg['svcs'][i], cap=cfg['caps'][i],
                                   waiting=[], in_svc=[None] * cfg['cs'][i],
                                   queues=[[] for _ in range(cfg['cs'][i])]))
        if cfg['routing'] == 'stage_swap' and cfg['nodes'] == 2:
            self.nodes.reverse()
            for _i, _nd in enumerate(self.nodes):
                _nd['idx'] = _i        # 事件堆用 idx 索引节点，换序后必须重编
        self.leave_after = 0 if cfg['routing'] == 'drop2nd' else cfg['nodes'] - 1
        self.split_mode = cfg['split'] in ('random', 'jockey') and self.nodes[0]['c'] > 1

    # ---- 面积积分：必须在任何状态改变之前调用；与 win_start 取交集
    def integ(self):
        if self.t_now > self.last:
            lo = max(self.last, self.ws)
            if self.t_now > lo:
                dt = self.t_now - lo
                self.A['area'] += self.N * dt
                if self.N > 0:
                    self.A['nz'] += dt
            self.last = self.t_now

    def push(self, t, kind, ni, payload):
        self._seq += 1
        heapq.heappush(self.heap, (t, self._seq, kind, ni, payload))

    def draw_svc(self, nd):
        kind, mu = nd['svc'], nd['mu']
        if kind == 'det':
            return 1.0 / mu
        if kind == 'h2':
            h = h2_moments(mu, self.cfg['cv'])
            r = h['r1'] if self.rng.random() < h['p1'] else h['r2']
            return self.rng.expovariate(r)
        return self.rng.expovariate(mu)

    def lam_t(self, t):
        lam = self.cfg['lam']
        if self.cfg['arrivals'] == 'timevary':
            lam = lam * (1.0 + TIMEVARY_AMP * math.sin(2.0 * math.pi * t / TIMEVARY_PERIOD))
            lam = max(lam, 0.05 * self.cfg['lam'])
        return lam

    def next_gap(self, t):
        if self.cfg['arrivals'] == 'determ':
            return 1.0 / self.cfg['lam']
        return self.rng.expovariate(self.lam_t(t))

    # ---- 到达事件
    def on_arrival(self, t):
        nb = BATCH_N if self.cfg['arrivals'] == 'batch' else 1
        for _ in range(nb):
            if self.split_mode:
                self.admit_split(t)
            else:
                self.admit(0, t)
        self.push(t + self.next_gap(t), 'arr', 0, None)

    def admit(self, ni, t, carry=None):
        """进入节点 ni：到达时抽服务时长 → integ() → 改状态。"""
        nd = self.nodes[ni]
        self.t_now = t
        cust = carry
        if cust is None:
            self.cid += 1
            cust = dict(cid=self.cid, arrival=t, elapsed=0.0)
        cust['svc'] = self.draw_svc(nd)
        cust['elapsed'] = 0.0
        cap = nd['cap']
        mode = self.cfg['cap_mode']
        self.integ()
        inw = t >= self.ws
        # 原来这里无条件 +1，于是两节点串联题里 arr = 外部到达 + 内部转移 = 2n，
        # 而 dep 只数离开系统 = n ⇒ J2b 流量守恒 |arr−dep−blk|/arr 恒等于 0.5，
        # 把正确的参照件判成守恒破坏。单节点题 carry 永远是 None，所以这次改动不影响它们。
        if inw:
            if carry is None:
                self.A['arr'] += 1
            else:
                self.A['arr_in'] += 1
        blocked = False
        if cap is not None:
            if mode == 'system':
                blocked = self.N >= cap
            elif mode == 'queue_as_system':
                blocked = len(nd['waiting']) >= cap
            # none / no_baulk_action / minus3(已折进 cap 值) → 不阻塞或按新 cap
        if blocked:
            self.A['blk'] += 1 if inw else 0
            return
        self.N += 1
        j = self.free_server(nd)
        if j < 0:
            self.A['waits'] += 1 if inw else 0
            if self.cfg['patience'] == 'abandon':
                dl = t + self.rng.expovariate(1.0 / (ABANDON_MEAN_MULT / nd['mu']))
                self.push(dl, 'reneg', ni, cust['cid'])
        if self.cfg['discipline'] in ('lcfs_pr', 'lcfs_restart') and j < 0:
            vj, victim = self.oldest_in_service(nd)
            if victim is not None:
                self.A['trig_preempt'] += 1
                self.release_busy(nd, vj, t)
                victim['elapsed'] += t - victim['start']
                if self.cfg['discipline'] == 'lcfs_restart':
                    victim['elapsed'] = 0.0
                nd['in_svc'][vj] = None
                nd['waiting'].append(victim)
        nd['waiting'].append(cust)
        self.pump(nd)

    def free_server(self, nd):
        for j, c in enumerate(nd['in_svc']):
            if c is None:
                return j
        return -1

    def oldest_in_service(self, nd):
        bj, bc = -1, None
        for j, c in enumerate(nd['in_svc']):
            if c is not None and (bc is None or c['start'] < bc['start']):
                bj, bc = j, c
        return bj, bc

    def release_busy(self, nd, j, t):
        c = nd['in_svc'][j]
        self.A['busy'] += max(0.0, t - max(c['start'], self.ws))

    def pick_index(self, nd):
        """返回被选中顾客在 waiting 里的**下标**（不是对象）。
        用 list.remove(obj) 在发散型队列里是 O(N)，整套 dir 会被 E04/E25 拖到 O(N^2)；
        这里 fcfs/lcfs/预占/siro 都是 O(1)，只有 spt/priority_class 需要扫描。
        选取规则与语义完全不变（平手时取最先出现者，与 min 一致）。
        末尾的 trig_* 只**观测**这次选取，不参与任何计算 ⇒ 加了计数器不该动任何读数，
        这条由 `check_trig_no_side_effects.py` 用受控 A/B 钉住（逐位不变才算通过）。"""
        w = nd['waiting']
        d = self.cfg['discipline']
        if d == 'fcfs':
            bi = 0
        elif d == 'lcfs' or d in ('lcfs_pr', 'lcfs_restart'):
            bi = len(w) - 1
        elif d == 'siro':
            bi = self.rng2.randrange(len(w))
        elif d == 'spt':
            bi, bv = 0, None
            for i, c in enumerate(w):
                v = (c['svc'] - c['elapsed'], c['arrival'])
                if bv is None or v < bv:
                    bv, bi = v, i
        elif d == 'priority_class':
            ms = 1.0 / nd['mu']
            bi, bv, n0 = 0, None, 0
            for i, c in enumerate(w):
                cls = 0 if (c['svc'] - c['elapsed']) < ms else 1
                n0 += (cls == 0)
                v = (cls, c['arrival'])
                if bv is None or v < bv:
                    bv, bi = v, i
            self.A['trig_class0'] += n0
        else:
            raise ValueError(d)
        if bi != 0 and len(w) > 1:
            self.A['trig_nonhead'] += 1
        return bi

    def pump(self, nd):
        while nd['waiting']:
            j = self.free_server(nd)
            if j < 0:
                return
            cust = nd['waiting'].pop(self.pick_index(nd))
            self.start(nd, cust, j)

    def start(self, nd, cust, j):
        self.gen += 1
        cust['srv_j'] = j
        cust['start'] = self.t_now
        cust['gen'] = self.gen
        nd['in_svc'][j] = cust
        rem = max(0.0, cust['svc'] - cust['elapsed'])
        self.push(self.t_now + rem, 'done', nd['idx'], (j, self.gen))

    def record_departure(self, ni, cust, t):
        """只有**离开口径点（最后一个节点）**的顾客才计入 W 样本与 dep 计数；
        串联网络中间节点的离开不是"离开系统"。"""
        if ni < self.leave_after:
            return
        if t >= self.ws:
            dup = self.cfg['counting'] == 'double_dep' and self.rng2.random() < DOUBLE_DEP_P
            self.A['dep'] += 2 if dup else 1
            s = t - cust['arrival']
            self.A['soj'].append(s)
            if dup:
                self.A['soj'].append(s)

    def on_done(self, ni, j, gen, t):
        nd = self.nodes[ni]
        cust = nd['in_svc'][j]
        if cust is None or cust.get('gen') != gen:
            return                              # 抢占后的过期事件
        self.t_now = t
        self.A['busy'] += max(0.0, t - max(cust['start'], self.ws))
        if self.cfg['sched'] == 'server_leak':
            # E41：顾客照样离开，但槽位不置空 ⇒ 服务台被永久吃掉一台。
            # 把幽灵标记成过期(gen 不匹配)，防同一槽位上的后续事件重复计离开。
            self.A['trig_leak'] += 1
            cust['gen'] = -1
        else:
            nd['in_svc'][j] = None
        self.integ()
        self.N -= 1
        self.record_departure(ni, cust, t)
        if self.cfg['state'] == 'junk':
            self.A['junk'] += 1
        if ni < self.leave_after:
            self.A['trig_transfer'] += 1        # 只观测：E20(stage_swap) 这类注入是否真有转派可被换序
            self.admit(ni + 1, t, dict(cid=cust['cid'], arrival=cust['arrival'],
                                       elapsed=0.0))
        self.pump(nd)

    def on_reneg(self, ni, cid, t):
        self.t_now = t
        nd = self.nodes[ni]
        target = None
        for c in nd['waiting']:
            if c['cid'] == cid:
                target = c
                break
        self.integ()
        if target is None:
            return
        nd['waiting'].remove(target)
        self.N -= 1
        self.A['lost'] += 1 if t >= self.ws else 0
        self.pump(nd)

    # ---- 分队路径（E19/E23）
    def shortest_server(self, nd):
        best, bj = 1 << 30, 0
        for j in range(nd['c']):
            L = len(nd['queues'][j]) + (1 if nd['in_svc'][j] is not None else 0)
            if L < best:
                best, bj = L, j
        return bj

    def admit_split(self, t):
        nd = self.nodes[0]
        self.t_now = t
        self.cid += 1
        cust = dict(cid=self.cid, arrival=t, elapsed=0.0)
        cust['svc'] = self.draw_svc(nd)
        self.integ()
        inw = t >= self.ws
        self.A['arr'] += 1 if inw else 0
        if nd['cap'] is not None and self.cfg['cap_mode'] == 'system' and self.N >= nd['cap']:
            self.A['blk'] += 1 if inw else 0
            return
        self.N += 1
        j = (self.rng2.randrange(nd['c']) if self.cfg['split'] == 'random'
             else self.shortest_server(nd))
        if nd['in_svc'][j] is not None:
            self.A['waits'] += 1 if inw else 0
            if self.cfg['patience'] == 'abandon':
                dl = t + self.rng.expovariate(1.0 / (ABANDON_MEAN_MULT / nd['mu']))
                self.push(dl, 'reneg', 0, cust['cid'])
        nd['queues'][j].append(cust)
        if nd['in_svc'][j] is None:
            self.start_split(nd, j)

    def start_split(self, nd, j):
        q = nd['queues'][j]
        if not q:
            return
        cust = q.pop(0) if self.cfg['discipline'] == 'fcfs' else q.pop()
        self.gen += 1
        cust['start'] = self.t_now
        cust['gen'] = self.gen
        cust['srv_j'] = j
        nd['in_svc'][j] = cust
        self.push(self.t_now + max(0.0, cust['svc'] - cust['elapsed']), 'done', 0, (j, self.gen))

    def on_done_split(self, j, gen, t):
        nd = self.nodes[0]
        cust = nd['in_svc'][j]
        if cust is None or cust.get('gen') != gen:
            return
        self.t_now = t
        self.A['busy'] += max(0.0, t - max(cust['start'], self.ws))
        nd['in_svc'][j] = None
        self.integ()
        self.N -= 1
        if t >= self.ws:
            dup = self.cfg['counting'] == 'double_dep' and self.rng2.random() < DOUBLE_DEP_P
            self.A['dep'] += 2 if dup else 1
            s = t - cust['arrival']
            self.A['soj'].append(s)
            if dup:
                self.A['soj'].append(s)
        if self.cfg['state'] == 'junk':
            self.A['junk'] += 1
        self.start_split(nd, j)

    def on_reneg_split(self, cid, t):
        self.t_now = t
        nd = self.nodes[0]
        for q in nd['queues']:
            for c in q:
                if c['cid'] == cid:
                    self.integ()
                    q.remove(c)
                    self.N -= 1
                    self.A['lost'] += 1 if t >= self.ws else 0
                    return

    def on_jock(self, t):
        self.t_now = t
        nd = self.nodes[0]
        qs = nd['queues']
        hi = max(range(nd['c']), key=lambda j: len(qs[j]))
        lo = min(range(nd['c']), key=lambda j: len(qs[j]))
        if len(qs[hi]) >= len(qs[lo]) + 2:
            self.integ()
            qs[lo].append(qs[hi].pop())
            if qs[lo] and nd['in_svc'][lo] is None:
                self.start_split(nd, lo)
        self.push(t + JOCKEY_DT, 'jock', 0, None)

    def run(self):
        self.push(self.next_gap(0.0), 'arr', 0, None)
        if self.split_mode and self.cfg['split'] == 'jockey':
            # 只维持**一条**自续的换队时钟链：每个到达各开一条会变成 O(n_arr * H/dt) 条事件，
            # mmc__e23 因此在 H=5000 上跑到 600s 超时（自检抓到后修的）。
            self.push(JOCKEY_DT, 'jock', 0, None)
        self.integ()
        while self.heap:
            tt, _, kind, ni, payload = heapq.heappop(self.heap)
            if tt >= self.H:
                break
            if kind == 'arr':
                self.on_arrival(tt)
            elif kind == 'done':
                if self.split_mode:
                    self.on_done_split(payload[0], payload[1], tt)
                else:
                    self.on_done(ni, payload[0], payload[1], tt)
            elif kind == 'reneg':
                if self.split_mode:
                    self.on_reneg_split(payload, tt)
                else:
                    self.on_reneg(ni, payload, tt)
            elif kind == 'jock':
                self.on_jock(tt)
        self.t_now = self.H
        self.integ()
        self.A['win'] = self.win
        return self.A


def run_once(cfg, seed, horizon):
    return Sim(cfg, seed, horizon).run()


# ------------------------------------------------------------------ 库存模板
def run_newsvendor(cfg, seed, days):
    p = cfg['params']
    mu_d, sd = float(p['mu_d']), float(p['sd'])
    price, cost, salvage = float(p['price']), float(p['cost']), float(p['salvage'])
    opt = cfg['inv_opt']
    cu, co = price - cost, cost - salvage
    if opt == 'cuco_swap':
        cu, co = co, cu
    if opt == 'no_salvage':
        co = cost
        salvage_used = 0.0
    else:
        salvage_used = salvage
    if opt == 'mean_instead':
        q = mu_d
    else:
        q = mu_d + norm_ppf(cu / (cu + co)) * sd
    rng = random.Random(seed)
    vals = []
    junk = 0
    lo = int(cfg['window'] * days)
    for i in range(days):
        d = mu_d if opt == 'demand_determ' else rng.gauss(mu_d, sd)
        sales = d if d < q else q
        prof = price * sales - cost * q + salvage_used * (q - sales)
        junk += 1
        if i >= lo:
            vals.append(prof)
    if cfg['state'] != 'junk':
        junk = 0
    return dict(q=q, profit_vals=vals, junk=junk)


def newsvendor_stats(cfg, seed, days):
    r = run_newsvendor(cfg, seed, days)
    v = r['profit_vals']
    return r['q'], (sum(v) / len(v) if v else float('nan'))


def run_eoq(cfg, n, horizon):
    p = cfg['params']
    D, S, H = float(p['D']), float(p['S']), float(p['H'])
    if cfg['time_base'] == 'annual_to_daily':
        D, H = D / UNIT_SCALE_DAYS, H / UNIT_SCALE_DAYS
    form = cfg['eoq_form']
    if form == 'no_factor2':
        q = math.sqrt(D * S / H)
    elif form == 'swap_SH':
        q = math.sqrt(2.0 * D * H / S)
    else:
        q = math.sqrt(2.0 * D * S / H)
    lost = 0.0
    if cfg['solver'] == 'rate_from_own_order_count':
        # E42：出口报的不是闭式 q*，而是"窗口里数出的订货次数"反推的需求率算出的 q̂
        # （真实标本 eoq-02__d1.py:60）。丢掉的正好是不满一轮的那一段 ⇒ floor 的残量。
        cycles = D * EOQ_RATE_WINDOW_YEARS / q
        orders = int(cycles)
        lost = cycles - orders
        d_hat = q * orders / EOQ_RATE_WINDOW_YEARS
        q = math.sqrt(2.0 * d_hat * S / H)
    cost = D / q * S + (q * H if form == 'hold_full_qty' else q / 2.0 * H)
    return dict(q=q, cost=cost, trig_lostcycle=lost)


# ------------------------------------------------------------------ KPI 汇总
def apply_pert_cfg(cfg, name):
    """角色扰动（J4 用）。配方与 calib_ref/*__REF.py::apply_pert 逐字一致：
       lam×1.15 / mu×1.25 / c+1 / cap-1，除此之外什么都不动。
       以前 criteria.py 会传 --pert 但这里用 parse_known_args 静默丢掉，
       于是"扰动件"其实跑的是基线 ⇒ dW 恒等于 0 ⇒ 会被读成一条假盲区。"""
    if name in (None, '', 'none'):
        return cfg
    if name == 'lam_up':
        cfg['lam'] = float(cfg['lam']) * 1.15
    elif name == 'mu_up':
        cfg['mus'] = [m * 1.25 for m in cfg['mus']]
    elif name == 'c_up':
        cfg['cs'] = [c + 1 for c in cfg['cs']]
    elif name == 'cap_down':
        cfg['caps'] = [max(2, k - 1) if k is not None else None for k in cfg['caps']]
    else:
        raise SystemExit('unknown pert %s' % name)
    cfg['pert'] = name
    return cfg


def kpi(task, etype='REF', n=20, horizon=40000.0, seed_start=1, pert='none'):
    cfg = apply_pert_cfg(resolve(task, etype), pert)
    seeds = list(range(seed_start, seed_start + n))
    if task['template'] == 'eoq':
        r = run_eoq(cfg, n, horizon)
        return dict(q=r['q'], cost=r['cost'], seeds=seeds,
                    per_seed={'q': [r['q']] * n, 'cost': [r['cost']] * n},
                    trig_lostcycle=r['trig_lostcycle'],
                    runtime_units='years', seeds_used=n)
    if task['template'] == 'newsvendor':
        stats = [newsvendor_stats(cfg, s, int(horizon)) for s in seeds]
        per_seed = [p_ for _, p_ in stats]
        m, hw, df = t_ci(per_seed)
        return dict(q=stats[0][0], exp_profit=m, exp_profit_hw=hw, ci_df=df,
                    reps=per_seed, seeds=seeds,
                    per_seed={'exp_profit': per_seed, 'q': [stats[0][0]] * n},
                    runtime_units='days', seeds_used=n)
    reps = [run_once(cfg, s, horizon) for s in seeds]
    ctot = sum(cfg['cs'])
    soj, areas, busys, occs = [], [], [], []
    arr = arr_in = dep = blk = waits = lost = 0
    trig = dict(nonhead=0, preempt=0, class0=0, transfer=0, leak=0)
    win_sum = 0.0
    for r in reps:
        w = r['win']
        win_sum += w
        areas.append(r['area'] / w)
        soj.append(sum(r['soj']) / len(r['soj']) if r['soj'] else float('nan'))
        busys.append(r['busy'] / (w * ctot))
        occs.append(r['nz'] / w)
        arr += r['arr']
        arr_in += r.get('arr_in', 0)
        dep += r['dep']
        blk += r['blk']
        waits += r['waits']
        lost += r['lost']
        for kk in trig:
            trig[kk] += r.get('trig_' + kk, 0)          # 跨种子累计：触发 0 次 = 注入没落地
    # ---- 出口算子（E39/E40/E43）：砸的是**每条种子的源序列**，不是只砸聚合字段。
    #      真实工件里 `pw = 0.0` / `busy = 0` 是每种子共用的同一个变量，只改均值会让
    #      per_seed_* 与聚合同时就打脸——那是仪器自造的矛盾读数（10-18 §18 刚栽过一次）。
    backsolved = (cfg['estimator'] == 'little_backsolve')
    if cfg['field_const'] == 'zero_W':
        soj = [0.0] * len(soj)
    elif backsolved:
        soj = [(a_ / (r['dep'] / r['win'])) if r['dep'] else float('nan')
               for a_, r in zip(areas, reps)]
    if cfg['field_const'] == 'zero_busy':
        busys = [0.0] * len(busys)
    W = sum(soj) / len(soj)
    if backsolved:
        # 聚合口单独钉：J2a 吃的是**聚合**的 L 与 dep_rate，若取"每种子反推值再平均"
        # 会留下 Jensen 残量，声明里写的"恒等"就变成"接近恒等"。
        W = (sum(areas) / len(areas)) / (dep / win_sum)
    wf = float(cfg.get('w_out_factor', 60.0))   # 内部时间单位 -> 契约的分钟
    pw_ps = [(r['waits'] / r['arr']) if r['arr'] else 0.0 for r in reps]
    pl_ps = [(r['blk'] / r['arr']) if r['arr'] else 0.0 for r in reps]
    # `busy_frac` 取哪一个由**契约声明**决定（见 resolve() 里的 busy_def）：
    #   'occupied'   -> 1−π₀（站不空的时间比例）
    #   'util'       -> E[min(N,c)]/c（每台平均利用率）
    #   'coincident' -> c=1 时两式恒等，取哪个都一样（这里取 util）
    bd = cfg.get('busy_def')
    has_busy_truth = (task.get('truth_raw') or {}).get('busy_frac') is not None
    if bd is None and has_busy_truth:
        raise SystemExit('%s 的真值里有 busy_frac 却没声明定义 ⇒ 题集缺 busy_def，'
                         '先重生成 tasks.jsonl（bench.py），不许在这里猜口径' % cfg['task_id'])
    if bd is None:
        # jackson2 这类题没有忙度真值：报哪个口径都不进 J1 计分，取 util 只为出口字段完整。
        bd = 'util'
    if bd not in ('util', 'occupied', 'coincident'):
        raise SystemExit('%s 的 busy_def=%r 不是三个合法值之一' % (cfg['task_id'], bd))
    use_occ = (bd == 'occupied')
    busy_ps = occs if use_occ else busys
    _, hwW, df = t_ci([s for s in soj])
    _, hwL, _ = t_ci(areas)
    busy_field = (sum(occs) / len(occs)) if use_occ else (sum(busys) / len(busys))
    out = dict(W_min=W * wf, L=sum(areas) / len(areas),
               busy_frac=busy_field, busy_util=sum(busys) / len(busys),
               busy_occupied=sum(occs) / len(occs),
               p_wait=waits / arr if arr else 0.0,
               p_loss=blk / arr if arr else 0.0,
               lam_hat=dep / win_sum, arr_hat=arr / win_sum,
               # 窗口内的流量账：到达 = 离开 + 满员被拒 + 中途放弃（+ 边界余项）。
               # mmcK 实测 blk>0 而 lost=0，只按 lost 算会把正确件判成守恒破坏，
               # 守恒残差必须由判据(J2b)去判，不能在这里预先把差异抹平。
               cons=abs(arr - dep - blk - lost) / arr if arr else 0.0,
               W_hw=hwW * wf, L_hw=hwL, ci_df=df,
               p_wait_hw=t_ci(pw_ps)[1], p_loss_hw=t_ci(pl_ps)[1],
               busy_hw=t_ci(busy_ps)[1], busy_frac_hw=t_ci(busy_ps)[1],
               per_seed=dict(p_wait=pw_ps, p_loss=pl_ps, busy=busy_ps,
                             W=[s * 60.0 for s in soj], L=list(areas)),
               runtime_units=cfg.get('internal_unit', 'hours'), seeds_used=n,
               seeds=seeds,
               # ---- 诊断量（内核早就算好了，以前在出口被丢掉）----
               arr_avg=arr / n, dep_avg=dep / n, blk_avg=blk / n, lost_avg=lost / n,
               arr_in_avg=arr_in / n,
               waits_avg=waits / n, win_avg=win_sum / n,
               warmup_units=WARM_DEFAULT * horizon,
               c=sum(cfg['cs']) / len(cfg['cs']), K=cfg['caps'][0],
               dist_arr=cfg['arrivals'], dist_svc=cfg['svcs'][0],
               n_nodes=cfg['nodes'], pert=cfg.get('pert', 'none'),
               # ---- 触发计数（P-02/P-03）：恒等类的"没检出"要有机制真跑过的证据 ----
               trig_nonhead=trig['nonhead'], trig_preempt=trig['preempt'],
               trig_class0=trig['class0'], trig_transfer=trig['transfer'],
               trig_leak=trig['leak'],
               # 出口算子是**静态覆盖**，没有运行期分支可数，所以计数取"被覆盖的种子序列条数"：
               # 0 条 = 这一支根本没走到，≥1 = 落地。它和 trig_leak 那种事件计数不同源，
               # 汇总端 IDLE 判定要按算子类型分开看（见 summarize_matrix_v2.IDLE_GATE）。
               trig_fieldconst=(n if cfg['field_const'] in ('zero_W', 'zero_busy') else 0),
               trig_backsolve=(n if backsolved else 0),
               # stage_swap 在两个节点参数完全相同时是**字面空操作**（reverse 看不出来），
               # 这一条静态判定和运行计数互补：jackson2-03 的 mu1=mu2=10、s1=s2=6 就属此类。
               trig_swap_noop=1 if (cfg['routing'] == 'stage_swap' and cfg['nodes'] == 2
                                    and cfg['mus'][0] == cfg['mus'][1]
                                    and cfg['cs'][0] == cfg['cs'][1]
                                    and cfg['svcs'][0] == cfg['svcs'][1]) else 0,
               W_per_seed=[s * wf for s in soj], L_per_seed=list(areas))
    return out


# ------------------------------------------------------------------ CLI
def _r6(x):
    if x is None or isinstance(x, str) or isinstance(x, bool):
        return x
    if isinstance(x, int):
        return x                       # 整数就是整数，别让 round 把 seeds_used 变成 5.0
    try:
        v = round(float(x), 6)
    except (TypeError, ValueError):
        return x
    # 算不出来的观测量（窗口内一次离开都没有）发 null，不发 NaN：
    # NaN 会让 `nan > tau` 恒 False ⇒ "判不了"被读成"检不出"，而且 NaN 不是合法 JSON。
    # 发 null 之后 criteria 走 field_missing ⇒ 如实记 NA。现存 346 件不产生 NaN
    # （MUTANT_MATRIX_R10b.shard*.csv 里 'nan' 出现 0 次），所以这条改动对旧格是惰性的。
    if v != v or v in (float('inf'), float('-inf')):
        return None
    return v


# runtime_units('hours'/'days'/'years') -> criteria._UNIT_HOURS 认的单数名
_TIME_UNIT = {'hours': 'hour', 'minutes': 'minute', 'days': 'day', 'years': 'year'}


def contract_out(task, k):
    out = {}
    for key in task['output_contract']:
        if key == 'W':
            out['W'] = k['W_min']
        elif key == 'L':
            out['L'] = k['L']
        elif key in ('p_loss', 'p_wait', 'busy_frac'):
            out[key] = k[key]
        elif key == 'q':
            out['q'] = k['q']
        elif key in ('exp_profit', 'cost'):
            out[key] = k[key]
        else:
            raise KeyError(key)
    out['runtime_units'] = k['runtime_units']
    out['seeds_used'] = k['seeds_used']
    # 排队题的三个概率量一律报出来，不管这道题的 output_contract 点没点名：
    # J2c（忙度≤1）与 J3a（利用率/PASTA 配对）都要吃 busy_frac，缺了就整条判不了。
    # ⚠ 对称性要求（腿 B 的提示词必须同样要这几个字段，否则参照件报 25 个字段、
    #    LLM 工件只报 4 个，J2/J3 会在 LLM 侧白送通过率——那是假公平）。
    for o in ('p_loss', 'p_wait', 'busy_frac'):
        if o not in out and k.get(o) is not None:
            out[o] = k[o]
    # ---- P0 扩展契约（INTERFACE_GAPS §1）。全是透传，不重新计算：
    #      以前 kpi() 把 arr/dep/blk/win/每种子序列都算好了，是出口把它们扔了，
    #      于是 J2/J3/J4 一律 field_missing（判不了 ≠ 判过）。
    out['time_unit'] = _TIME_UNIT.get(k['runtime_units'], 'hour')
    ps = k.get('per_seed') or {}
    if 'arr_avg' in k:                      # 排队题才有流量与窗口
        out['arr'] = k['arr_avg']
        out['arr_internal'] = k.get('arr_in_avg', 0.0)
        out['dep'] = k['dep_avg']
        out['blk'] = k['blk_avg']
        out['lost'] = k['lost_avg']
        out['win'] = k['win_avg']
        out['dep_rate'] = k['lam_hat']
        out['lam_eff'] = k['lam_hat']
        out['warmup_units'] = k['warmup_units']
        out['cons_dev'] = k['cons']
        # 忙度有两个合法口径，必须分开报，不能让一个名字背两种定义：
        #   busy_util     = E[min(N,c)]/c  每台平均利用率   （J3a 要的是这个）
        #   busy_occupied = 1 − π0         至少一台在忙     （mmcK 真值用的是这个）
        # c=1 时两者重合，所以混淆只在多服务台+有限容量上暴露（实测见 criteria.j3_pairing 注释）。
        out['busy_util'] = k.get('busy_util')
        out['busy_occupied'] = k.get('busy_occupied')
        # 触发计数一律报出（参照件与变异件都要）：汇总端靠它把"注入没落地"的件从分母里挑出去。
        # 只报原始计数、不做判断——判断在 `summarize_matrix_v2.py` 的 INJECTION_IDLE 档里。
        for nm in ('trig_nonhead', 'trig_preempt', 'trig_class0', 'trig_transfer',
                   'trig_swap_noop', 'trig_leak', 'trig_fieldconst', 'trig_backsolve'):
            out[nm] = k.get(nm)
    # 确定式题（eoq）也有机制计数，且它不在上面那个"只有排队题才有"的分支里：
    # E42 的空转证据 = 被 floor() 丢掉的周期残量，0 表示这道题压根不产生偏差。
    if k.get('trig_lostcycle') is not None:
        out['trig_lostcycle'] = k['trig_lostcycle']
    out['seed_list'] = k.get('seeds')
    for nm, src in (('per_seed_W', 'W'), ('per_seed_L', 'L'),
                    ('per_seed_p_loss', 'p_loss'), ('per_seed_p_wait', 'p_wait'),
                    ('per_seed_busy_frac', 'busy'), ('per_seed_exp_profit', 'exp_profit'),
                    ('per_seed_q', 'q')):
        if src in ps and ps[src] is not None:
            out[nm] = [_r6(v) for v in ps[src]]
    for nm in ('c', 'K', 'dist_arr', 'dist_svc', 'n_nodes', 'pert'):
        if k.get(nm) is not None:
            out[nm] = _r6(k[nm])
    return {kk: _r6(vv) for kk, vv in out.items()}


def main(task_id=None, etype='REF', argv=None):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('--seeds', type=int, default=20)
    ap.add_argument('--horizon', type=float, default=40000.0)
    ap.add_argument('--seed-start', dest='seed_start', type=int, default=1)
    ap.add_argument('--pert', default='none')
    a, unused = ap.parse_known_args(argv)
    if unused:
        # 严格回执：criteria.py 传的每个参数都必须真被用上。
        # 静默丢参的坏处不是崩，而是把接口断掉伪装成"这条判据看不见"的实测结论。
        raise SystemExit('unknown artifact args: %r' % (unused,))
    task = task_by_id()[task_id]
    k = kpi(task, etype, n=a.seeds, horizon=a.horizon,
            seed_start=a.seed_start, pert=a.pert)
    sys.stdout.write(json.dumps(contract_out(task, k)) + '\n')
    return 0


if __name__ == '__main__':
    argv = sys.argv[1:]
    tid = argv[0] if argv and not argv[0].startswith('--') else 'mm1-01'
    et = argv[1] if len(argv) > 1 and not argv[1].startswith('--') else 'REF'
    rest = [x for i, x in enumerate(argv) if i >= 2]
    sys.exit(main(tid, et, rest))
