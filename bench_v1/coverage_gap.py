"""① 覆盖差表：用**真实工件自己犯的错**反向审计**我注入的错型谱**。

这张表要回答的问题不是"我的判据能检出多少"（那是 186/186 那张主表），而是：
    **我的注入谱本身漏了大模型真会犯的哪些类、又过量造了哪些类它们根本不犯的？**
左边那半是"基准自己的缺陷清单"，右边那半是"我为什么造了这么多没用的变异体"。

2026-10-18 这张表闭环了一次：缺口清单里的 6 类中 **5 类已做成真算子**加进 `simcore.ERRORS`
（E39 常量发报 / E40 源变量从不置位 / E41 事件调度不释放 / E42 数值不收敛 / E43 自证式估计），
所以它从现在起不只是"描述"，而是"审计完之后把漏的补上、再看检出率怎么变"。
类数与件数一律现读（`injected_side()`），不手写。

⚠ 关于"没人做过"这句：**2026-10-18 正文级查新回来了，答案是这个动作已被占**
（最接近的是 arXiv:2610.22089v1，用量子软件的 410 条真实缺陷审计四个变异测试工具的算子谱，
报"只有 56/410=13.7% 落在被表示的错型族里"；另有 arXiv:2512.16741v2 的 expressiveness gap、
arXiv:2112.14508v1 的 Defects4J 覆盖率）。 ⇒ **禁写"首次/没人做过"**，
只能写"把 representation-gap 审计范式迁移到 LLM 生成仿真模型的自动判分谱"，
缝隙是三件事同时成立：被审计的是**判分仪器**的注入谱、真实错误来自 **LLM 自己写的随机仿真模型**、
覆盖差与逐格判据能力边界表闭环。详见 `空白声明账_2026-10-18.md`。

数据的四个来源，全部现读、不手抄：
 1. 注入侧：`simcore.ERRORS` + `simcore.CATALOG`（family/short）+ `artifacts/*__eNN.py` 实数件数；
 2. 真实侧·格级：`LEGB_RESULT.md` 的 (3) 归族表（按 `报/真` 倍数）；
 3. 真实侧·源码模式：`REAL_ERROR_TAXONOMY.md` 的计数表（件级）；
 4. 跨语料对照：`REAL_ERROR_TAXONOMY.md` 的跨语料行（两种口径：连散文 / 只扫代码）。

⚠ 三条纪律，写在表里也要印出来：
 · **映射是我的人工判断，不是从数据推出来的** ⇒ 每行给"判定依据"，供他/另一个 AI 逐条推翻；
 · **"真实没有"有两种**：我这批语料检不到 vs 真的不发生。正则漏检（尤其"发常量 0"和"变量从不置位"
   这两类需要数据流分析，正则不可靠）⇒ 只能写"本轮未检到"，不许写"真实不存在"；
 · 件与格不许混：注入侧数**件**，真实侧既有**件**（源码模式命中）又有**格**（报警观测量），
   每一格数字后面都带单位。
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import simcore as S          # noqa: E402


# ───────────────────────── 1. 注入侧（盘上现读）
def injected_side():
    fam = defaultdict(list)
    for eid, d in (S.CATALOG or {}).items():
        fam[d.get('family') or '?'].append((eid, d.get('short') or '', d.get('expected') or ''))
    files = [f for f in os.listdir(os.path.join(HERE, 'artifacts'))
             if f.endswith('.py') and '__REF' not in f]
    n_file = Counter(re.search(r'__e(\d+)\.py$', f).group(0) for f in files if re.search(r'__e(\d+)\.py$', f))
    per_e = Counter()
    for f in files:
        m = re.search(r'__e(\d+)\.py$', f)
        if m:
            per_e['E' + m.group(1)] += 1
    return fam, per_e, len(files)


# ───────────────────────── 2. 真实侧·格级（LEGB_RESULT.md 的 (3) 表）
def cells_families():
    p = os.path.join(HERE, 'LEGB_RESULT.md')
    out = {}
    if not os.path.exists(p):
        return out
    for ln in io.open(p, encoding='utf-8'):
        m = re.match(r'^\| ([^|]+?) \| (\d+) \| ([\d.]+)% \|', ln)
        if m and ('×' in m.group(1) or '报=0' in m.group(1) or '符号' in m.group(1)):
            out[m.group(1).strip()] = int(m.group(2))
    return out


# ───────────────────────── 3. 真实侧·源码模式（REAL_ERROR_TAXONOMY.md 的计数表）
def pattern_counts():
    p = os.path.join(HERE, 'REAL_ERROR_TAXONOMY.md')
    out = {}
    if not os.path.exists(p):
        return out
    for ln in io.open(p, encoding='utf-8'):
        m = re.match(r'^\| `([A-Za-z_0-9]+)` \| (\d+) \| ([\d.]+)% \|', ln)
        if m:
            out[m.group(1)] = int(m.group(2))
    return out


# ───────────────────────── 4. 跨语料对照行（两种口径的命中数，现读不手抄）
def corpus_rows():
    p = os.path.join(HERE, 'REAL_ERROR_TAXONOMY.md')
    out = {}
    if not os.path.exists(p):
        return out
    for ln in io.open(p, encoding='utf-8'):
        m = re.match(r'^\| `([^`]+)` \| (\d+) \| (\d+) \| [\d.]+% \| (\d+) \| [\d.]+% \|', ln)
        if m:
            out[m.group(1)] = dict(n=int(m.group(2)), prose=int(m.group(3)), code=int(m.group(4)))
    return out


# ───────────────────────── 5. 环节映射（**人工判断，可被逐条推翻**）
# key = 注入侧 family；real = 真实侧证据（模式名/格族名 + 一句依据）
# verdict ∈ SAME(同机制覆盖) / DIFF(同环节异机制) / INJ_ONLY(注入独有=过量造) /
#           REAL_ONLY(真实独有=谱缺口) / TBD(本轮未判定，原因写在 why)
MAP = {
    'order': dict(verdict='SAME', real=[('rem_not_decremented', '件级')],
                  why='E01–E04/E25 都是"调度/抢占规则"层。E25(预占后剩余时长不更新) 与真实的 '
                      '`rem` 不递减是**同一机制**，但前提不同：E25 需要抢占才会触发，'
                      '真实工件在 FCFS 非预占下就犯了（实例 `mh2-01__d3.py:51/:86`）'
                      '⇒ 谱里有这一机制，但**触发前提被我设高了**。'
                      '**2026-10-18 已补**：非预占那一支现在由 `E41`(family=scheduling) 独立承载'),
    'priority': dict(verdict='TBD', real=[],
                     why='真实侧本轮未检到"优先级分类写错"的实例；但 jackson2/mmcK 的报警格成因还没'
                         '逐件人读 ⇒ 只能写"未检到"，不能写"不发生"'),
    'resource': dict(verdict='SAME', real=[('rate_mean_swap', '件级')],
                     why='E07(λ↔μ 互换) 对上真实的 `expovariate` 传均值（1 件）；'
                         'E05/E06(服务台数写错) 真实侧未检到 ⇒ 这一族是**半覆盖**'),
    'arrival_service_process': dict(verdict='TBD', real=[],
                                    why='E09–E13 是"分布族选错"。真实侧 mh2 一致率 0/48 说明确实有东西错了，'
                                        '但我还没把人读结论落到"哪一件把 H2 写成什么" ⇒ 判定悬空'),
    'capacity_blocking': dict(verdict='TBD', real=[],
                              why='mmcK 一致率 1.3%（76 格只 1 格一致）——真实侧大量偏离，'
                                  '但成因未拆到行；不能据此说"覆盖了 E14–E16/E21"'),
    'routing': dict(verdict='TBD', real=[],
                    why='jackson2 一致率 11.5%，报警格多但成因未逐件人读'),
    'split': dict(verdict='EMPTY_GROUP', real=[], why='这一行**不是**"没有这类变异体"，而是我上一条记错了：'
                  '`ERRORS` 里的键是 **hook**（E19=`split:random`、E23=`split:jockey`），'
                  '`CATALOG` 里的 `family` 是**语义分组**，两者本来就不要求一致：'
                  'E19 我按"网络里的分流"记进 `routing`、E23 按"顾客行为"记进 `customer_behaviour`。'
                  '⇒ 按 family 计数这一行就是 0 类，按 hook 数则是 2 类 22 件。'
                  '**我先前把它写成"同一份标签两处权威"是错的**（那是两种切法，不是两处权威），'
                  '这里更正；要核 hook 口径请看 `simcore.ERRORS`'),
    'customer_behaviour': dict(verdict='TBD', real=[],
                              why='真实侧需要"漏实现放弃/换队"这类证据；本轮 8 件人读没覆盖到'),
    'estimation': dict(verdict='DIFF', real=[('warm_numerator_mismatch', '件级'),
                                             ('W_not_measured', '件级'),
                                             ('wait_area_zero_only', '件级')],
                       why='**这一族是本表最重要的一格**：环节同名（都是"估计/观测怎么算"），'
                           '机制完全不同。我注入的是"窗口长度取错(E26/E30)、计数重复(E27)、'
                           '单位同倍换算(E28/E35)、多余的死变量(E29)"；'
                           '真实犯的是"**分子全期累加 / 分母只用稳态窗口**"21 件、'
                           '**W 根本不测量、拿 Little 反推**38 件、**等待面积只写 `+= 0.0` 占位**12 件。'
                           '⇒ 同一环节、谱与现实的交集比我以为的小得多。'
                           '**2026-10-18 已补**：后两类做成 `E39`(常量发报) 与 `E43`(自证式估计)，'
                           '另外真实那一族"源变量从不置位"补成 `E40`；'
                           '`warm_numerator_mismatch`(分子全期/分母窗口) 仍**没补**——它需要的是'
                           '面积累加时机，不是出口覆盖，留作下一批'),
    'inventory': dict(verdict='INJ_ONLY', real=[('(EOQ 死循环)', '件级')],
                      why='E31–E34/E36–E38 共 7 类全是**公式层**（Cu/Co 用反、漏系数 2、S 与 H 互换…），'
                          '而真实侧 newsvendor 一致率 94.4%、eoq 96.9%，公式层几乎不犯；'
                          '真实那一族的错发生在**实现层**（eoq 有 2 件写成死循环、66 行/124 行就 420 s 超时）'
                          '⇒ 我在这族过量造变异体，同时漏掉了它真正会错的方向。'
                          '**2026-10-18 部分已补**：实现层那一支补成 `E42`(family=numerics)'),
    # ---- 2026-10-18 新增的两个 family：都是"真实有、谱里整族没有"补出来的 ----
    'scheduling': dict(verdict='NOW_COVERED', real=[('rem_not_decremented', '件级')],
                       why='`E41` 服务台槽位离开后不置空（资源泄漏）。真实侧 7/192 件。'
                           '预演读数：L 随 H 线性发散（mm1-01 在 H=2000→8000 时 5003→19911）、'
                           'J2b 流量守恒恒等于 1、窗口内一次离开都没有 ⇒ W 发 null 记 NA。'
                           '**这一类在注入谱里曾是整族空白**，因为我的谱全建在"语义/参数错"上，'
                           '没有"执行层样板错"这一支'),
    'numerics': dict(verdict='NOW_COVERED', real=[('(EOQ 死循环)', '件级')],
                     why='`E42` 需求率从自己数出的订货次数反推（真实标本 `eoq-02__d1.py:60`）。'
                         '这一类的可检性**与样本预算无关**（确定式解），只由题面参数决定：'
                         '偏差 = 1−√(⌊D/q*⌋/(D/q*))，题集 6 题里 4 题的 D/q* 恰为整数 ⇒ 偏差**精确 0** '
                         '⇒ 按空转剔除。剩下的 2 题 q 偏 5.43%（可检）、cost 只偏 0.156%（不可检）。'
                         '⚠ 真实那 2 件的形态是永不退出 ⇒ 工件无读数，**进不了判据分母**，'
                         '这条如实写成"注入谱对程序跑不完这一族是结构性覆盖不到"'),
}

# 真实侧有、注入谱整族没有的（这就是"谱缺口"清单）
# 第 4 个字段 = 2026-10-18 的处置（补成了哪个算子 / 为什么补不了），空转与预期一并写清。
GAPS = [
    ('常量发报', '把某个观测量直接写成常量（实例 `mm1-02__d1.py:94` 的 `pw = 0.0`）',
     '注入谱里没有任何"输出字段=常量"这一类；正则不可靠（要数据流：该变量的常量值会被 '
     '累加进 per_* 再平均），所以**只能人读定件**，本轮定到 1 件 ⇒ 计数标"仅人读"',
     '**已补 `E39`**(W 发 0，14 件) 与 **`E40`**(busy 发 0，14 件)。'
     'E39 两个模板外推：J1|W 与 J2a 都等于 1.0；E40 有 2/7 个模板是 blind（口径切法所致，见 CATALOG）'),
    ('源变量从不置位', '初始化 `busy = 0` 之后再没被赋值，于是 `busy_frac` 精确等于 0'
     '（实例 `md1-01__d1.py:36`，经 :71/:148/:155 传到输出）',
     '与我的 E29 方向**正好相反**：E29 造的是"加了用不上的状态变量"（无害的死代码），'
     '真实犯的是"该更新的变量没更新"（有害的死变量）⇒ 谱里有一格长得像但不是它',
     '**已补 `E40`**：砸的是 util 那条**源**，不是只砸聚合字段（否则 per_seed 与均值自相矛盾）'),
    ('服务不释放/队列发散', '事件推进时不递减剩余服务时间 ⇒ 服务台永远做不完（`mh2-01__d3.py:51/:86`，'
     'L 报 36002 vs 真值 0.509，7 万倍）',
     'E25 只覆盖"抢占后"这一支，非预占下也犯 ⇒ 谱缺"基础事件调度写错"这一整支',
     '**已补 `E41`**(14 件，新 family=scheduling)；机制计数器 `trig_leak` 是真事件计数'),
    ('数值实现不收敛/死循环', '闭式题被写成迭代且不收敛（eoq 两件 420 s 超时）',
     '注入谱全部是"语义错"，没有一类是"程序跑不完/跑不对但语法合法"——'
     '而这恰是 LLM 工件特有的错型来源',
     '**部分已补 `E42`**(6 件，新 family=numerics)：建模的是"循环退出了、把未收敛值报出来"那一支；'
     '**永不退出那一支补不了**——它没有读数，进不了判据分母，只能落链条的 CRASH/TIMEOUT 档 ⇒ '
     '这条如实写成"注入谱对这一族的覆盖是结构性的，不是检不出"'),
    ('契约字段语义读错', '`runtime_units` 被填成数字（153/192 件，主形态 40000.0 = 本次 horizon）',
     '注入谱只注**数值**错，不注**输出契约字段语义**错 ⇒ 它直接让我的两条判据腿(J0a/J0e)在真实工件上失声',
     '**未补**：J0 不在主表分母里（规矩 23），补成注入件只会造出一堆 NA 而不是检出证据；'
     '处置方式是 `unit_violation` 留痕 + 词表补齐(ms/day/year)，属口径治理不属错型谱'),
    ('自证式估计', 'W 用 Little 定律从 L 反推（38 件）⇒ 与判据 J2a 同源',
     '这一类不是"模型算错了"，而是"**这条判据对它恒真**"⇒ 属仪器盲区，注入谱里也没有'
     '"验证器与被验对象共用同一假设"这一类',
     '**已补 `E43`**(14 件) 并**预期 blind**：J2a 残差被压到出口舍入位(实测 2.5e-8~8.2e-7)，'
     'J1|W 与 J1|L 同源 ⇒ 加大预算只会更不显著。这是第二型不可检（自证型），'
     '与 E01/E02/E20 的定理型不同：**换一套判据就能消掉**'),
]


def main():
    fam, per_e, n_files = injected_side()
    cells = cells_families()
    pat = pattern_counts()
    corp = corpus_rows()
    inj_types = sum(len(v) for v in fam.values())
    NEW5 = ('E39', 'E40', 'E41', 'E42', 'E43')
    n_new = sum(per_e.get(e, 0) for e in NEW5)
    L = ['# 注入错型谱 vs 真实错型谱：覆盖差表（反向审计基准自己的标签）', '']
    L.append('> 主语料：腿 B flash 批 192 件（`_flash_v2_items.txt`，R=10/40000）；'
             '注入侧 %d 类 / 盘上 %d 件变异体实数，其中 **%d 件是 2026-10-18 由这张表反向补出来的 '
             '%d 类**（%s）。' % (inj_types, n_files, n_new, len(NEW5), '、'.join(NEW5)))
    L.append('> **注入侧计数已双向核对**：`ERRORS` 与 `CATALOG` 同为 %d 类、盘上 %d 件逐类对齐'
             '（0 缺 0 余，由 `_newop_gen_verify.py` 现算并给退出码）。'
             '历史作废两条：①我先前口头说过"38 类"，那是按 E01–E38 连号脑算的，实测是 37；'
             '②我曾把 `split` 一行写成"同一份标签两处权威"，那是**两种切法**（hook vs family）'
             '被我当成两处权威，见该行的依据列。' % (inj_types, n_files))
    if corp:
        inj_c = corp.get('artifacts') or {}
        L.append('> **本表的映射列是人工判断**，不是从数据推出的；每行附"判定依据"供逐条推翻。'
                 '另：真实错型目录的检测器**跨语料不可复用**——同一套正则跑注入语料 %d 件，'
                 '连散文扫命中 %d 件、只扫代码命中 %d 件'
                 '（那 %d 件是我把真实标本的代码写进注入工件的 docstring 当出处造成的假阳，'
                 '已记在 `REAL_ERROR_TAXONOMY.md`）。⇒ 本表的"真实侧"只描述腿 B 那批工件的写法，'
                 '不是普适错型频率。'
                 % (inj_c.get('n', 0), inj_c.get('prose', 0), inj_c.get('code', 0),
                    inj_c.get('prose', 0)))
    else:
        L.append('> **本表的映射列是人工判断**，不是从数据推出的；每行附"判定依据"供逐条推翻。'
                 '⚠ `REAL_ERROR_TAXONOMY.md` 里没解析到跨语料对照行 ⇒ 本条**没核**，'
                 '不许据此写"检测器跨语料不可复用"。')
    L.append('')
    L.append('## (1) 逐环节对账')
    L.append('')
    L.append('| 环节(注入侧 family) | 注入类数 | 注入件数 | 真实侧证据（件/格） | 判定 | 依据 |')
    L.append('|---|---|---|---|---|---|')
    ORDER = ['order', 'priority', 'resource', 'arrival_service_process', 'capacity_blocking',
             'routing', 'split', 'customer_behaviour', 'estimation', 'inventory',
             'scheduling', 'numerics']
    tag = {'SAME': '同机制覆盖', 'DIFF': '同环节·异机制', 'INJ_ONLY': '**注入独有（过量造）**',
           'REAL_ONLY': '**真实独有（谱缺口）**', 'TBD': '本轮未判定',
           'EMPTY_GROUP': '按 family 数是空组（分组选择，不是缺件）',
           'NOW_COVERED': '**真实独有 → 已补成算子**'}
    for k in ORDER:
        items = fam.get(k, [])
        m = MAP[k]
        ev = []
        for name, unit in m['real']:
            if name.startswith('('):
                ev.append('%s' % name)
            elif name in pat:
                ev.append('`%s` %d 件' % (name, pat[name]))
            else:
                ev.append('`%s`' % name)
        L.append('| `%s` | %d | %d | %s | %s | %s |' % (
            k, len(items), sum(per_e.get(e[0], 0) for e in items),
            '；'.join(ev) or '本轮未检到', tag[m['verdict']], m['why']))
    L.append('')
    L.append('## (2) 真实侧的偏差形状（格级，来自 `LEGB_RESULT.md` (3)）')
    L.append('')
    for k, v in sorted(cells.items(), key=lambda x: -x[1]):
        L.append('- `%s` %d 格' % (k, v))
    L.append('')
    L.append('**读法**：量纲族（60× / 1÷60×）合计只有 %d 格，而我注入谱里 `rate_units`+`time_base`'
             '两类就造了 4 类 %d 件 ⇒ **"LLM 建模主要栽在单位换算上"是被我的谱造出来的假象**，'
             '这句从今天起禁写。' % (cells.get('60×(分↔时)', 0) + cells.get('1/60×(时↔分)', 0),
                                    sum(per_e.get(e, 0) for e in ('E07', 'E08', 'E28', 'E35'))))
    L.append('')
    closed = sum(1 for g in GAPS if g[3].startswith('**已补') or g[3].startswith('**部分已补'))
    L.append('## (3) 谱缺口清单与处置（%d 类，其中 %d 类已补成真算子）' % (len(GAPS), closed))
    L.append('')
    L.append('| # | 缺口 | 真实侧证据 | 为什么谱里没有 / 计数可靠度 | 2026-10-18 处置 |')
    L.append('|---|---|---|---|---|')
    for i, (name, desc, why, action) in enumerate(GAPS, 1):
        L.append('| %d | **%s** | %s | %s | %s |' % (i, name, desc, why, action))
    L.append('')
    L.append('> 补完之后**必须**重跑 stage2 + 主表，报"加新算子后逐格检出率怎么变"；'
             '这张表当前只到"算子已上线 + 单点预演通过"，主表那一列还空着。')
    L.append('')
    L.append('## (4) 过量造清单：注入有、真实几乎不发生')
    L.append('')
    L.append('- 公式层库存错型 7 类（`inventory`）：真实侧同族一致率 94.4–96.9%，公式层几乎不犯；')
    L.append('- 量纲/单位换算类：真实侧 4/392 格；')
    L.append('- "多余的死变量"E29：与真实的"该更新没更新"方向相反，**看着像覆盖其实没覆盖**。')
    L.append('')
    L.append('## (5) 要让这张表变成结论，还欠什么（不写成就不能说"审计过了"）')
    L.append('')
    L.append('1. **人读要扩**（未完成）：本轮 8 件（5 件到行级）；缺口清单里 3 类靠单件实例立论 ⇒ 至少要'
             '每模板 ≥2 件、并把"常量发报/从不置位"这两类的件数用**人工或 AST 遍历**数出来'
             '（正则不可信，今天又实测了一台：注入语料连散文扫 14/408 全是我自己的 docstring 造成的假阳）；')
    L.append('2. **反向补注入**（算子已完成，主表未重跑）：`%s` 共 %d 类 %d 件已进 `simcore.ERRORS` '
             '并通过单点预演（`_newop_smoke.md`，REF 无副作用预检 25 格逐位相同）；'
             '**"加了新算子后逐格检出率怎么变"这个数要等链跑完才有**，在那之前这张表仍然只是描述。'
             % ('、'.join(NEW5), len(NEW5), n_new))
    L.append('3. **第二语料**（未动）：航空参数 5–8 题（D1）上看同一族缺口是否再现，'
             '否则"谱有缺口"也可能是"我的抽象题集有偏"；')
    L.append('4. **查新**（已完成，结论是**不利的那一面**）："用真实错误反向审计注入式错误谱"这个'
             '**动作已被占**——最接近的是 arXiv:2610.22089v1（2026-10-15，用量子软件的 410 条真实缺陷'
             '审计 4 个变异测试工具 + 3 个缺陷基准，报"只有 56/410 = 13.7% 落在被表示的错型族里"），'
             '另有 arXiv:2512.16741v2（数据故障仿真的 expressiveness gap）与 arXiv:2112.14508v1'
             '（各注入手段对 Defects4J 真实缺陷的语义覆盖率）。 ⇒ **禁写"首次/没人做过"**；'
             '可辩护的缝隙只剩"三件事同时成立"：被审计的是**判分仪器**的注入谱、'
             '真实错误来自 **LLM 自己写的随机仿真模型**、覆盖差与逐格能力边界表闭环。'
             '措辞降级为"把 representation-gap 审计范式迁移到 LLM 生成仿真模型的自动判分谱"。')
    L.append('')
    L.append('## (6) 一句话差分（可辩护，不是"我们不同"）')
    L.append('')
    L.append('变异测试的算子集是在**人写的代码**上标定出来的，其错型集中在规范/语义层；'
             'LLM 生成工件的错型集中在**执行层样板**（占位赋值、变量从不置位、事件调度不释放、'
             '迭代不收敛、用被测对象的输出反推被测对象的判据）⇒ 算子谱不能直接搬，'
             '需要按生成端重新标定。本表 (1)(3) 就是这次重新标定的账。')
    L.append('')
    out = os.path.join(HERE, 'COVERAGE_GAP.md')
    io.open(out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('inj_types=%d inj_files=%d cells_families=%d patterns=%d gaps=%d -> %s'
          % (inj_types, n_files, len(cells), len(pat), len(GAPS), os.path.basename(out)))


if __name__ == '__main__':
    main()
