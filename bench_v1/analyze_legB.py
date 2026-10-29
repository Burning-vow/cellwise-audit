"""腿 B 判分结果的落表器：读 `_rejudge_flash20261018.txt` 的逐件记录，出六张表。

为什么单独一个文件（不在终端里 grep 出数就写进正文）：本机老规矩——计数要落 .py，
要能被别人重跑复核；而且这里每一条数都要能对回**出处字段**。

三件必须分开报的事（混了就是一句假结论）：
 1. **三门槛**（可编译 / 契约字段齐全 / 参照可比率）：判"flash 能不能撑起腿 B"；
 2. **口径违规 153 件**（自报 `time_unit` 是词表外的数字，多为 horizon 40000）：
    那是**仪器失声**（J0a/J0c/J2a/J3a 同时 NA），既不是工件合格、也不是工件写错；
 3. **报警格**（报的值与闭式真值差超 τ*）：这才是"真实大模型写的模型不合格"的信号，
    但它必须先按 `报/真` 的**倍数**拆开——落在 60× / 3600× 附近的是**量纲错型**，
    落在 τ*~2τ* 的是估计噪声或轻度偏差，两类在论文里是两个不同的句子。

用法：~/miniconda3/python.exe analyze_legB.py [_rejudge_flash20261018.txt]
输出：LEGB_RESULT.md（UTF-8；控制台只打计数核对行，中文不进 GBK 控制台）
"""
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criteria as C        # noqa: E402  词表要取自判分器本身，不许分析脚本另列一份

CELL = re.compile(r'^(?P<obs>\S+) 报=(?P<est>-?[\d.eE+-]+) 真=(?P<truth>-?[\d.eE+-]+) '
                  r'rel=(?P<rel>-?[\d.]+)% τ\*=(?P<tau>[\d.]+) (?P<verdict>报警|一致)$')
BADUNIT = re.compile(r'^口径违规\((?P<fld>time_unit|runtime_units)=(?P<val>.*?) 在词表外')
# 兼容 2026-10-18 19:55 那代旧文案（两个字段并成一句、且把失声面夸成四条）：只用来读旧报告，
# 新报告一律走上面这条带字段名的格式。字段不明的旧行记成 'unknown_field'，绝不混进分字段计数。
BADUNIT_OLD = re.compile(r'^口径违规：自报单位在词表外 \[(?P<vals>[^\]]*)\]')


def derive_kind(r):
    """老版报告（19:55 那一跑由改前脚本产出）逐件记录里**没有 kind 字段**。
    这里按与 rejudge_existing.judge_one 完全相同的分支顺序把它推回来，
    并在 main 里与报告头的『分型』逐档对账——对不上就是我这里推错，不是它数错。"""
    if r.get('kind'):
        return r['kind']
    if 'syntax_err' in r:
        return 'SYNTAX'
    if not r.get('agree'):
        return 'NO_ENTRY' if not r.get('has_entry') else 'CRASH'
    return 'FIELD_GAP' if r.get('missing_fields') else 'OK'


def header_kinds(path):
    """从报告头的『## 分型』取脚本自己数的档数（当独立出口用）。"""
    out = {}
    inside = False
    for ln in io.open(path, encoding='utf-8'):
        s = ln.rstrip('\n')
        if s.startswith('## 分型'):
            inside = True
            continue
        if inside:
            if s.startswith('##') and '分型' not in s:
                break
            m = re.match(r'^- (\w+): (\d+)$', s)
            if m:
                out[m.group(1)] = int(m.group(2))
    return out


def load(path):
    recs = []
    for ln in io.open(path, encoding='utf-8'):
        ln = ln.strip()
        if ln.startswith('{'):
            recs.append(json.loads(ln))
    for r in recs:
        r['kind_derived'] = 'kind' not in r      # 老版报告没有这一列，是我推的
        r['kind'] = derive_kind(r)
    return recs


def cls_ratio(est, truth):
    """把'报/真'的倍数归到错型族。返回 (倍数, 族名)。

    ⚠ 桶必须**穷尽**。第一版这里只有一个"其他大偏差"兜底桶，实测吃掉报警格的 40%
    ——那种桶等于没分，所以按 |倍数| 数量级切细，并把"报=0"单拎出来
    （那多半是**这一项根本没报**，与"报了但差 3 倍"是两个不同的句子）。
    """
    if truth == 0:
        return None, '真=0（比值无意义）'
    if est == 0:
        return 0.0, '报=0（这一项没报出来）'
    r = est / truth
    if r < 0:
        return r, '符号相反'
    for name, k in (('60×(分↔时)', 60.0), ('3600×(秒↔时)', 3600.0), ('24×(时↔天)', 24.0),
                    ('1/60×(时↔分)', 1 / 60.0), ('1/3600×(时↔秒)', 1 / 3600.0),
                    ('1/24×(天↔时)', 1 / 24.0)):
        if abs(r - k) / k < 0.02:
            return r, name
    if 0.99 <= r <= 1.01:
        return r, '±1% 内（刚超 τ*）'
    if 1.01 < r <= 1.5 or 0.67 <= r < 0.99:
        return r, '近阈值带（1–1.5×）'
    if 1.5 < r <= 3 or 0.33 <= r < 0.67:
        return r, '中等（1.5–3×）'
    if 3 < r <= 10 or 0.1 <= r < 0.33:
        return r, '大（3–10×）'
    if 10 < r <= 100 or 0.01 <= r < 0.1:
        return r, '极大（10–100×）'
    return r, '离谱（>100×）'


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else '_flash_v2_items.txt'
    # ⚠ 默认源**必须是 sidecar（拼接件）**，不是 `_rejudge_*.txt` 正文：`summarize()` 为了控体积
    #    把 `cells` 从正文的逐件行里剔掉了 ⇒ 拿正文当输入时 (2) 那节会**静默显示 0 条违规**，
    #    看着像"真实工件都不违规"，其实是我读了一份不含该字段的文件。
    #    而且默认值一度指着 v1（措辞作废代），一跑就把好的 LEGB_RESULT.md 覆盖回去。两个都是自伤。
    path = src if os.path.isabs(src) else os.path.join(HERE, src)
    recs = load(path)
    no_cells = [r for r in recs if 'cells' not in r]
    assert recs, '读不到任何逐件记录：%s' % path
    if len(no_cells) == len(recs):
        sys.stderr.write('%s 里没有 cells 字段 ⇒ (2) 口径违规一节无从计算；请改用 sidecar（如 _flash_v2_items.txt）\n'
                         % os.path.basename(path))
    files = [r['file'] for r in recs]
    assert len(files) == len(set(files)), '重复件名 ⇒ sidecar/报告被写过两遍'
    kinds = Counter(r.get('kind') or 'NONE' for r in recs)
    L = []
    w = L.append

    # ── (0) 记录完整性
    n = len(recs)
    hd = header_kinds(path)
    bad = {k: (v, kinds.get(k, 0)) for k, v in hd.items() if v != kinds.get(k, 0)}
    assert not bad, '我推的分型与报告头对不上 %s ⇒ 停下，别把推出来的档数当读数' % bad
    w('# 腿 B 判分结果（源：%s）' % os.path.basename(path))
    w('')
    w('读入 **%d 件**（件名唯一）｜分型：%s' % (n, json.dumps(dict(kinds), ensure_ascii=False)))
    w('')
    if not hd:
        w('> 输入是 **sidecar（逐件 JSONL）**，里面本来就带 `kind` 列 ⇒ 没有报告头可对账；'
          '分型直接取记录，`load_sidecars` 的重复键断言负责保证分片没切重。')
    elif any(r.get('kind_derived') for r in recs):
        w('> ⚠ 本份的分型列**不全是记录里读来的**：报告由改前脚本产出，逐件记录没有 `kind`，'
          '这里按 `judge_one` 的同一分支顺序反推，并已与报告头『## 分型』逐档对账通过：%s。'
          % json.dumps(hd, ensure_ascii=False))
    else:
        w('> 分型直接取自逐件记录的 `kind` 列；与报告头『## 分型』逐档对账通过：%s。'
          % json.dumps(hd, ensure_ascii=False))
    w('')

    # ── (1) 三门槛
    comp = n - kinds['SYNTAX']
    okreq = kinds['OK']
    withobs = [r for r in recs if r.get('agree')]
    cmpf = [r for r in withobs if int(r['agree'].split('/')[1]) > 0]
    allagree = [r for r in cmpf if r['agree'].split('/')[0] == r['agree'].split('/')[1]]
    nc_in = sum(int(r['agree'].split('/')[0]) for r in withobs)
    nc_tot = sum(int(r['agree'].split('/')[1]) for r in withobs)
    w('## (1) 预注册三门槛（对线 10-17 本地 8B 探针）')
    w('')
    w('| 门槛 | flash 实测 | 门槛 | 判 | 10-17 本地 8B / DeepSeek 旧探针 |')
    w('|---|---|---|---|---|')
    w('| 可编译 | %d/%d = %.1f%% | ≥80%% | %s | 8B 14/14=100%%（可编译这关一直不难） |'
      % (comp, n, 100.0 * comp / n, '过' if 100.0 * comp / n >= 80 else '不过'))
    w('| 契约字段齐全 | %d/%d = %.1f%% | ≥60%% | %s | 8B 11/14=78.6%% |'
      % (okreq, n, 100.0 * okreq / n, '过' if 100.0 * okreq / n >= 60 else '不过'))
    w('| 件级可比率（可比观测量全一致） | %d/%d = %.1f%% | ≥10%% | %s | 8B 探针只报过格级，件级无对照数 |'
      % (len(allagree), len(cmpf), 100.0 * len(allagree) / len(cmpf),
         '过' if 100.0 * len(allagree) / len(cmpf) >= 10 else '不过'))
    w('| **格级一致率**（主统计量） | %d/%d = %.1f%% | ≥10%% | %s | 8B 6/26=23.1%%、DeepSeek 5/46=10.9%% |'
      % (nc_in, nc_tot, 100.0 * nc_in / nc_tot, '过' if 100.0 * nc_in / nc_tot >= 10 else '不过'))
    w('')
    w('> ⚠ 门槛说的是"这台仪器在真实大模型工件上**比得出结果**"，不是"模型写得好"。')
    w('> 一致率 %.1f%% 的反面（报警 %.1f%%）才是腿 B 要的东西，但它要先按 (3) 拆错型才能当结论。'
      % (100.0 * nc_in / nc_tot, 100.0 * (nc_tot - nc_in) / nc_tot))
    w('')

    # ── (2) 口径违规，**按字段拆开**（字段↔判据是两条独立的失声面，不许并成一句）
    LEGS = {'runtime_units': 'J0a/J0e', 'time_unit': 'J0c/J2/J3'}
    vhit = defaultdict(set)          # 字段 → 命中的件名集合
    vals = defaultdict(Counter)      # 字段 → 自报取值分布
    old_style = 0                    # 旧文案（字段不明）命中数
    for r in recs:
        for c in (r.get('cells') or []):
            m = BADUNIT.match(c or '')
            if m:
                vhit[m.group('fld')].add(r['file'])
                vals[m.group('fld')][m.group('val')] += 1
            elif BADUNIT_OLD.match(c or ''):
                old_style += 1
    viol = sorted({f for s in vhit.values() for f in s})
    w('## (2) 口径违规：自报单位是词表外的生词（**仪器失声，不算合格也不算判错**）')
    w('')
    if no_cells:
        w('> ⚠ **本节无数据**：输入文件里没有 `cells` 字段（八成是读了 `_rejudge_*.txt` 正文而不是 '
          'sidecar），所以这里的 0 **不是**"没有违规"的结论。改用 `legB/.../_shard*.tsvl` 拼接件重跑。')
    w('| 字段 | 命中件（全体） | 命中件（能吐 JSON 的 %d 件内） | 被它关掉的判据 | 主形态 |' % len(withobs))
    w('|---|---|---|---|---|')
    for fld in ('runtime_units', 'time_unit'):
        s = vhit.get(fld) or set()
        sobs = {f for f in s if f in {r['file'] for r in withobs}}
        tv = vals[fld].most_common(1)
        w('| `%s` | %d/%d = %.1f%% | %d/%d = %.1f%% | **%s** | %r ×%d |' % (
            fld, len(s), n, 100.0 * len(s) / n,
            len(sobs), len(withobs), 100.0 * len(sobs) / len(withobs) if withobs else 0,
            LEGS[fld], tv[0][0] if tv else '-', tv[0][1] if tv else 0))
    both = vhit.get('runtime_units', set()) & vhit.get('time_unit', set())
    w('')
    w('- 两字段同时违规：%d 件 ｜**任一字段违规（去重件数）：%d/%d = %.1f%%**'
      % (len(both), len(viol), n, 100.0 * len(viol) / n))
    w('- 词表内合法单位（**取自 `criteria._UNIT_HOURS`，不是我列的**）：%s'
      % ', '.join(sorted(C._UNIT_HOURS)))
    if old_style:
        w('- ⚠ 本文件里 **%d 行是旧文案**（`口径违规：自报单位在词表外 [...]`，不带字段名）'
          '⇒ 那份报告把两个字段并成一句、并把失声面写成"四条"，**已作废，不许引用**；'
          '要引用就用改后重跑的那份。' % old_style)
    w('')
    w('> 读法（逐条回过 `criteria.py` 的行号，不是推测）：`criteria.py:290-291` 是全仓**唯一**读')
    w('> `runtime_units` 的地方 ⇒ 它只关掉 **J0a/J0e**；`time_unit` 走 `declared_unit_hours()`(:404)')
    w('> 与 :291 的 `htu` ⇒ 关掉 **J0c/J2/J3**。**J1（对闭式真值那条主判据）两个字段都不读**，')
    w('> 所以下面 (3) 的报警格统计**不受这些失声影响**——这也是"186/186 那批头条一格不动"的根据。')
    w('')

    # ── (3) 报警格的错型拆解
    fam = Counter()
    ex = defaultdict(list)
    obs_fire = Counter()
    obs_tot = Counter()
    n_fire = 0
    per_t = defaultdict(lambda: {'file': 0, 'cmp': 0, 'agree_file': 0, 'cell': 0,
                                 'in': 0, 'fire': 0, 'to': 0})
    for r in recs:
        t = r.get('template') or '?'
        per_t[t]['file'] += 1
        if r.get('run_note', '').find('timed out') >= 0:
            per_t[t]['to'] += 1
        for c in (r.get('cells') or []):
            m = CELL.match(c)
            if not m:
                continue
            est, truth = float(m.group('est')), float(m.group('truth'))
            tau, vd = float(m.group('tau')), m.group('verdict')
            per_t[t]['cell'] += 1
            obs_tot[m.group('obs')] += 1
            if vd == '一致':
                per_t[t]['in'] += 1
                continue
            per_t[t]['fire'] += 1
            obs_fire[m.group('obs')] += 1
            n_fire += 1
            # 归族**不再二次设 `rel>tau` 这道闸**：报警是判分器说的，我这里只负责说"差成什么形状"。
            # 原先加那道闸会用四位小数的 est/真值反推 rel，与判分器的高精度 rel 打架，
            # 结果是个别报警格静默掉出族外（分子少几格，还看不出来）。
            ratio, name = cls_ratio(est, truth)
            fam[name] += 1
            if len(ex[name]) < 3:
                ex[name].append('%s·%s 报=%.4f 真=%.4f 倍数=%s' % (
                    r['file'], m.group('obs'), est, truth,
                    ('%g' % ratio) if ratio is not None else '-'))
        if r.get('agree'):
            a, b = r['agree'].split('/')
            if int(b) > 0:
                per_t[t]['cmp'] += 1
                if a == b:
                    per_t[t]['agree_file'] += 1
    w('## (3) 报警格按 `报/真` 倍数归族（**别把量纲错和判据报警混成一句话**）')
    w('')
    w('- 报警格 **%d** ｜归入族 %d ｜差 **%d**%s'
      % (n_fire, sum(fam.values()), n_fire - sum(fam.values()),
         '（应当恒为 0；不为 0 说明有格没被归族，脚本会拒绝出表）' if n_fire != sum(fam.values()) else ''))
    tot_fire = sum(fam.values())
    w('')
    w('| 族 | 格数 | 占报警格 | 例（件·观测量·报/真·倍数） |')
    w('|---|---|---|---|')
    for k, v in fam.most_common():
        w('| %s | %d | %.1f%% | %s |' % (k, v, 100.0 * v / tot_fire if tot_fire else 0,
                                         '；'.join(ex[k])))
    w('')
    w('| 观测量 | 可比格 | 报警格 | 报警率 |')
    w('|---|---|---|---|')
    for o, tt in obs_tot.most_common():
        w('| %s | %d | %d | %.1f%% |' % (o, tt, obs_fire[o], 100.0 * obs_fire[o] / tt))
    w('')
    if n_fire != tot_fire:
        print('归族漏格：报警 %d 但归上 %d ⇒ 桶不穷尽，表不出' % (n_fire, tot_fire))
        sys.exit(3)

    # ── (4) 逐模板
    w('## (4) 逐模板（10-17 本地 8B 探针当时是"事件驱动 0/20"；flash 这边成不成立看这张）')
    w('')
    w('| 模板 | 件 | 可比件 | 全一致件 | 可比格 | 一致格 | 一致率 | 超时件 |')
    w('|---|---|---|---|---|---|---|---|')
    for t in sorted(per_t):
        d = per_t[t]
        rate = 100.0 * d['in'] / d['cell'] if d['cell'] else 0.0
        w('| %s | %d | %d | %d | %d | %d | %.1f%% | %d |'
          % (t, d['file'], d['cmp'], d['agree_file'], d['cell'], d['in'], rate, d['to']))
    w('')

    # ── (5) 失败件清单
    w('## (5) 不合格件清单（分型别混）')
    w('')
    for k in ('SYNTAX', 'NO_ENTRY', 'FIELD_GAP', 'CRASH'):
        rs = [r for r in recs if (r.get('kind') or '') == k]
        if not rs:
            continue
        w('- **%s（%d 件）**：%s' % (k, len(rs), ', '.join(r['file'] for r in rs)))
        if k == 'CRASH':
            tos = [r for r in rs if 'timed out' in (r.get('run_note') or '')]
            w('  - 其中**超时**（420 s 看门狗）%d 件：%s'
              % (len(tos), ', '.join('%s(%s 行)' % (r['file'], r.get('code_lines')) for r in tos)))
            w('  - 其余 %d 件是异常退出（不是超时）' % (len(rs) - len(tos)))
        if k == 'FIELD_GAP':
            for r in rs:
                w('  - %s 缺：%s' % (r['file'], r.get('missing_fields')))
    w('')

    # ── (6) 抽间稳定性：同一题三次抽是否同一命运
    w('## (6) 同题 3 抽的命运是否一致（这是"腿 B 每题必须 ≥3 抽"的直接证据）')
    w('')
    byt = defaultdict(list)
    for r in recs:
        tid = r['task_id']
        byt[tid].append('%s:%s' % (r.get('kind'), r.get('agree') or '-'))
    ident = sum(1 for tid, v in byt.items() if len(set(x.split(':')[1] for x in v)) == 1
                and len(set(x.split(':')[0] for x in v)) == 1)
    diff = [(tid, v) for tid, v in byt.items()
            if len(set(x.split(':')[1] for x in v)) > 1 or len(set(x.split(':')[0] for x in v)) > 1]
    w('- 64 题里 **3 抽命运完全相同**：%d 题；**至少一格不同**：%d 题' % (ident, len(diff)))
    w('- 前 8 个不同的例子：')
    for tid, v in diff[:8]:
        w('  - %s → %s' % (tid, ' | '.join(v)))
    w('')

    out = os.path.join(HERE, 'LEGB_RESULT.md')
    io.open(out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('n=%d kinds=%s viol=%d fire_cells=%d ok_cells=%d written=%s'
          % (n, dict(kinds), len(viol), sum(fam.values()), nc_in, out))


if __name__ == '__main__':
    main()
