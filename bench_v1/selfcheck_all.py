"""仪器自检总入口（论文"仪器自检"一节的**可执行版本**）。

为什么要有它：今天抓出来的每一条错，都不是靠"再跑一遍主实验"发现的，而是靠
拿已知正确的东西去对、或拿一条断言把两个量钉在一起。那种东西不该只写在报告里，
应该做成一条命令，任何人在改完代码之后跑一次就知道有没有把哪条闸碰坏。

每一项要么**当场重跑**对应脚本、要么**读它最近一次的产物**并在说明里给出重算命令；
不读任何"上一次自检"的缓存。输出只有 PASS/FAIL + 一条可追溯的数。
退出码：全过 0，任何一项不过 = 失败项数。不许有"沉默的跳过"——跳过的项必须计数并显示。

用法：~/miniconda3/python.exe selfcheck_all.py
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
P6 = os.path.join(HERE, '..', 'pilot_c6')


def data(name, env=None):
    """数据文件路径，允许用环境变量指到**合成副本**。

    为什么要有这个口子：审计的验收标准是"故意塞一行 gate=FAIL，总自检必须 FAIL"。
    不能为了验证闸而去动交付物；也不能只嘴上说"这条闸会响"。有了它，闸本身可测。
    """
    return os.environ.get('SC_' + (env or name), os.path.join(HERE, name))


def sh(cwd, args):
    """跑子脚本并取它最后一行当说明。

    ⚠ 必须显式给子进程 `PYTHONIOENCODING=utf-8`：Windows 控制台默认 cp936，
    子脚本 print 中文里的 `⚠`/`✓` 之类符号会先崩在编码上（rc=1），
    于是"第 2 项 FAIL"其实是**自检器自己在裸 shell 里跑不起来**（外部审计 F-9）。
    父端 capture 的解码与子端的编码是两件事，原来只设了前者。
    """
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    p = subprocess.run([PY] + args, cwd=cwd, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', env=env)
    tail = (p.stdout or '').strip().splitlines()
    return p.returncode, (tail[-1] if tail else (p.stderr or '').strip()[-160:])


def emit(s=''):
    """字节安全地往 stdout 写：控制台是 cp936 时 print('⇒') 会先崩在编码上，
    症状是 rc=1、'报告没生成'（其实文件已写好）——把工具自己的编码问题伪装成交付物失败。"""
    sys.stdout.buffer.write((str(s) + chr(10)).encode('utf-8', 'replace'))


def rows_of(path):
    n = 0
    with io.open(path, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                json.loads(line)          # 解析成功才算一行；wc -l 不是记录数
                n += 1
    return n


def csv_rows(path):
    with io.open(path, encoding='utf-8') as f:
        return list(__import__('csv').DictReader(f))


def undeclared_ref_dirs(root, min_files=5):
    """第 18 项的执行体：**除 `artifacts/` 外**，凡含 ≥`min_files` 份 `*__REF.py` 的目录，
    必须在自己目录里的 README.md 声明是历史出口（含'历史'或'勿用于现行判定'），否则列出来。

    为什么判"有没有声明"而不是判"两代内容是否一致"：历史代**本来就该不一样**
    （`calib_ref` 的 `runtime_units` 是计数、`artifacts` 是单位名，这正是两出口对账的价值所在），
    拿一致性当闸会在合法状态上长红——那只会逼人把它放宽。要防的是"**没人说它是历史**"，
    因为 10-18 晚我就是照 `criteria.py` 顶部那句旧权威声明去探 `calib_ref`，
    当场发出一条"stage1 表不可复现"的假警报（主表一格未动，但话已经发出去了）。
    """
    out = []
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d)
        if not os.path.isdir(p) or d == 'artifacts' or d.startswith('_'):
            continue                      # artifacts=现行权威；下划线开头=归档区，本就不当权威
        n = sum(1 for f in os.listdir(p) if f.endswith('__REF.py'))
        if n < min_files:
            continue
        rd = os.path.join(p, 'README.md')
        txt = ''
        if os.path.exists(rd):
            txt = io.open(rd, encoding='utf-8', errors='replace').read()
        if not (u'历史' in txt or u'勿用于现行判定' in txt):
            out.append('%s(%d 件,无声明)' % (d, n))
    return out


def main():
    checks = []

    # 1–2 报告里的数必须回得到 jsonl 上（机制独立的两条出口）
    for d, script, tag in ((P6, 'check_s33.py', '§3.3 的 2×2（36 个数）'),
                           (P6, 'check_s3.py', '§3 主表（24 个数）')):
        rc, msg = sh(d, [script])
        checks.append(('报告对账 ' + tag, rc == 0, msg[:150]))

    # 3 标定表与发射器必须同口径。
    #    ⚠ 这里原来只读 RECAL_CURRENCY.csv 的 status 字符串——那等于"拿一张旧快照当前证据"
    #    （外部审计 P-06③：criteria.py 15:06 改过，而这张表是 15:27 之前那次跑的）。
    #    改成**新鲜度断言**：残差表的 mtime 必须晚于所有会改变读数的源文件，否则本项 FAIL。
    #    （不在自检里重跑 check_recal_currency：它要 10 分钟，自检要能随手跑。改成断言"多久算过期"。）
    cur = data('RECAL_CURRENCY.csv')
    if os.path.exists(cur):
        rr = csv_rows(cur)
        # `IDENTICAL_NEWKEYS` = 值全部逐位相同、只是当前引擎多算出几条**新判据**的键（10-18 上 J0 就是这个情况）。
        # 把它当 DRIFT 等于"每加一条判据，64 题一起变红"，下一次就有人去把闸调松 —— 那是最坏的修法；
        # 但也不能当全等蒙过去，所以下面把 NEWKEYS 的行数**印出来**，让"多了什么"看得见。
        bad = [r for r in rr if not r['status'].startswith('IDENTICAL')]
        nkeys = [r for r in rr if r['status'] == 'IDENTICAL_NEWKEYS']
        srcs = ['criteria.py', 'simcore.py', 'bench.py', 'tasks.jsonl',
                'build_tables_v2.py', 'inv_obs.py']
        newest = max((os.path.getmtime(os.path.join(HERE, s)) for s in srcs
                      if os.path.exists(os.path.join(HERE, s))), default=0)
        stale = os.path.getmtime(cur) < newest
        stale_src = [s for s in srcs if os.path.exists(os.path.join(HERE, s))
                     and os.path.getmtime(os.path.join(HERE, s)) > os.path.getmtime(cur)]
        checks.append(('标定残差 vs 当前引擎（64 题逐位）',
                       len(rr) == 64 and len(bad) == 0 and not stale,
                       '行=%d（要求 64）；不全等 %d/%d 题；只多键不改值 %d 题%s' % (
                           len(rr), len(bad), len(rr), len(nkeys),
                           '' if not stale else '；但表已过期：改过 %s 之后没重跑 check_recal_currency.py'
                           % ','.join(stale_src))))
        # ⚠ `len(rr) == 64` 是 00:0x 现场补的：那次 `check_recal_currency` 正在写表（只落 25 行、
        #    mtime 还比所有源文件新），第 3 项照样报 PASS —— 这正是审计 P-08 说的"分母可缩"，
        #    只是这次缩在**我自己那道用来防它的闸**里。半截产物配新鲜 mtime = 一个会呼吸的假绿。
    else:
        checks.append(('标定残差 vs 当前引擎', False, 'RECAL_CURRENCY.csv 不存在，先跑 check_recal_currency.py'))

    # 4 阈值口径断言：τ* 的标定预算 == 门禁判定预算
    try:
        tau = csv_rows(os.path.join(HERE, 'table_tau_v2.csv'))
        basis = sorted({int(r['tau_basis_seeds']) for r in tau})
        src = io.open(data('run_p0_crosscheck.py', 'RUN_P0'), encoding='utf-8').read()
        seeds_line = [l for l in src.splitlines() if l.startswith('SEEDS =')]
        used = int(seeds_line[0].split('=')[1]) if seeds_line else None
        ok = len(basis) == 1 and used == basis[0]
        checks.append(('τ* 预算 == 门禁预算', ok, 'tau_basis_seeds=%s，run_p0_crosscheck SEEDS=%s' % (basis, used)))
    except Exception as e:                                   # noqa: BLE001
        checks.append(('τ* 预算 == 门禁预算', False, '读不到：%r' % (e,)))

    # 5 门禁自己不许含"未解析完"的表
    p0 = data('P0_CROSSCHECK.csv','P0')
    if os.path.exists(p0):
        rr = csv_rows(p0)
        col = 'gate' if rr and 'gate' in rr[0] else ('status' if rr and 'status' in rr[0] else None)
        cov = len({r['task_id'] for r in rr})
        blank = [r for r in rr if not col or not r.get(col)]
        g = __import__('collections').Counter(r.get(col) for r in rr) if col else {}
        #    ⚠ 原来只看"覆盖 64 题 + gate 列非空"，FAIL 计数只 print 不参与判定
        #    （审计 P-06①：往表里塞一行 gate=FAIL，总自检照样 PASS）。现在 FAIL 必须为 0。
        nfail = sum(v for k, v in g.items() if k not in ('PASS', 'NA', None, ''))
        # **重复键断言**（2026-10-18，他点单加进来的那条永久件）。
        #   为什么必须做在这里：`run_p0_crosscheck.py` 是**追加**写的，而"追加 + 被打断后重跑"
        #   与"续跑去重"在盘上看不出区别——只会让同一 (题,阶段,观测量,扰动) 出现两次。
        #   今天合盖暂停那一次，我是**手工**数出来 592 行=592 唯一键才敢继续的；
        #   手工数一遍不等于有闸，所以把它落到这里。重复行会让"计数"类结论静默膨胀。
        cnt = __import__('collections').Counter(
            (r.get('task_id'), r.get('stage'), r.get('obs'), r.get('pert')) for r in rr)
        ndup = sum(v - 1 for v in cnt.values() if v > 1)
        done = cov == 64 and not blank and nfail == 0 and ndup == 0
        checks.append(('stage1 门禁（覆盖 64 题、无空值、**FAIL=0**、无重复键）', done,
                       '列=%s 行=%d 唯一键=%d 重复行=%d 覆盖题数=%d/64 计数=%s FAIL=%d' % (
                           col, len(rr), len(cnt), ndup, cov, dict(g), nfail)))
    else:
        checks.append(('stage1 门禁（覆盖 64 题且判据无空值、无重复键）', False, 'P0_CROSSCHECK.csv 不存在'))

    # 6 良性件必须"自证良性"（这条是抓出 E28/E35 误标的闸）
    bp = data('BENIGN_PROOF.csv')
    if os.path.exists(bp):
        rr = csv_rows(bp)
        bad = [r for r in rr if r.get('verdict') != 'PROVES_BENIGN']
        #    ⚠ 分母原来是这张表**自报的行数**：成员从 74 缩到 68 无人拦（审计 P-06②/P-04）。
        #    现在与 `mutants.jsonl` 的 benign 集合做双向差集，谁少了都要响。
        try:
            labeled = set()
            for line in io.open(os.path.join(HERE, 'mutants.jsonl'), encoding='utf-8'):
                m = json.loads(line)
                if m.get('expected') == 'benign':
                    labeled.add((m['task_id'], m['error_type']))
            certified = {(r['task_id'], r['error_type']) for r in rr
                         if r.get('verdict') == 'PROVES_BENIGN'}
            only_lab = sorted(labeled - certified)
            only_cert = sorted(certified - labeled)
            same = not only_lab and not only_cert
            checks.append(('良性标签单一权威（mutants ≡ BENIGN_PROOF）', same,
                           '标 benign %d 件 / 自证通过 %d 件；只在标签里 %d 件%s；只在自证里 %d 件' % (
                               len(labeled), len(certified), len(only_lab),
                               (' 例 %s' % only_lab[:3]) if only_lab else '', len(only_cert))))
        except Exception as e:                               # noqa: BLE001
            checks.append(('良性标签单一权威（mutants ≡ BENIGN_PROOF）', False, repr(e)[:120]))
        checks.append(('良性对照自证闸', len(bad) == 0, '不过 %d/%d 件' % (len(bad), len(rr))))
    else:
        checks.append(('良性对照自证闸', False, 'BENIGN_PROOF.csv 不存在'))

    # 7 受控 A/B 的合法性：只改了 integ()，那么 W 与完成数必须逐位不变。
    #    ⚠ 原来这项是在 `RERUN_COMPARE.md` 里查字面量 '58/58'（审计 P-06④：报告改字就能骗过闸）。
    #    现在直接从两份 jsonl 重算，不看报告写了什么。
    cmp_new = os.environ.get('SC_PILOT_NEW') or os.path.join(P6, 'pilot_results.jsonl')
    cmp_base = os.environ.get('SC_PILOT_BASE') or os.path.join(P6, 'pilot_results.controlled_pre.jsonl')
    if os.path.exists(cmp_new) and os.path.exists(cmp_base):
        def keyd(p):
            out = {}
            for line in io.open(p, encoding='utf-8'):
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                out[(r.get('scene'), r.get('mut'), r.get('kind'))] = (
                    str(r.get('rel_W')), str(r.get('n')))
            return out
        a, b = keyd(cmp_new), keyd(cmp_base)
        common = sorted(set(a) & set(b))
        dw = [k for k in common if a[k][0] != b[k][0]]
        dn = [k for k in common if a[k][1] != b[k][1]]
        ok7 = bool(common) and not dw and not dn and len(a) == len(b) == len(common)
        checks.append(('受控 A/B：rel_W 与 n 逐位不变（重算，不读报告）', ok7,
                       '共同 %d 格；rel_W 变 %d 格；n 变 %d 格；两边行数 %d/%d' % (
                           len(common), len(dw), len(dn), len(a), len(b))))
    else:
        checks.append(('受控 A/B：rel_W 与 n 逐位不变', False,
                       '缺 %s 或 %s ⇒ 重跑 make_rerun_compare 的前置件' % (
                           os.path.basename(cmp_new), os.path.basename(cmp_base))))

    # 8 引擎不许有"同名两义"的字段被当同一个量用（J3a 那条的活闸）
    crit = io.open(data('criteria.py', 'CRIT'), encoding='utf-8').read()
    ok8 = "obs.get('busy_util')" in crit and 'busy_occupied' in io.open(
        data('simcore.py', 'SIM'), encoding='utf-8').read()
    checks.append(('busy 的两义已分开', ok8, 'criteria 读 busy_util、simcore 同时报 busy_util/busy_occupied'))

    # 9 字段契约必须逐题（2026-10-17 的 AE：全局清单向库存题索要 W/L，正确工件被判缺字段）
    try:
        import criteria as C                                        # noqa: E402
        import legB_grade as LG                                     # noqa: E402
        taus = LG.tau_map()
        tasks = C.load_tasks()
        leak, empty, uncov = [], [], []
        cmp_per_tpl = {}
        for (tpl, s) in taus:
            cmp_per_tpl.setdefault(tpl, []).append(s)
        for t in tasks:
            req, opt = LG.contract_fields(t, 'selfcheck')
            if t['template'] in ('eoq', 'newsvendor') and set(req) & {'W', 'L', 'p_wait', 'busy_frac'}:
                leak.append(t['task_id'])          # 全局清单混进库存题的形态，就是要抓的这个
            if not req:
                empty.append(t['task_id'])
            if not cmp_per_tpl.get(t['template']):
                uncov.append('%s(%s)' % (t['task_id'], t['template']))
        checks.append(('字段契约逐题（库存题不被索要排队字段）', not leak and not empty,
                       '题数=%d；向库存题索要排队字段的题=%s；契约空的题=%s' % (
                           len(tasks), leak[:4], empty[:4])))
        # 10 合成出口对每题都要有可比观测量（腿 B 曾因只走排队侧而对 eoq/newsvendor 是瞎的）
        checks.append(('每模板都有带 τ 星的观测量', not uncov,
                       '没有 τ 星行的题=%s（共 %d 题）' % (uncov[:5], len(uncov))))
    except Exception as e:
        checks.append(('字段契约逐题（库存题不被索要排队字段）', False, repr(e)[:140]))
        checks.append(('每模板都有带 τ 星的观测量', False, repr(e)[:140]))

    # 11 F3 余项的上界：正文钉的是 `m ≤ e·j`，那两条候选旧界必须**报出违例**才算复核过。
    #     为什么做成闸：`F3_M_DISTRIBUTION.md` 我给出 m 的分布却把 `m ≤ 该忙期人数` 直接写进预注册，
    #     一个忙期人数都没算（审计 F-2）⇒ 那条界被同一份数据否证（seed 54：m=21 > sz=17）。
    f3 = data('F3_BOUND_CHECK.md', 'F3')
    if os.path.exists(f3):
        txt = io.open(f3, encoding='utf-8').read()
        rr = [l for l in txt.splitlines() if l.startswith('| lcfs') or l.startswith('| siro')]
        num = [[int(x) for x in l.split('|')[3:7]] for l in rr]      # = [m≠0, B1违例, B2违例, B3违例]
        stream_ok = '不符数 = **0**' in txt
        b3_zero = all(c[3] == 0 for c in num)
        b2_fires = any(c[2] > 0 for c in num)      # 旧界必须"响"，否则说明这份报告是空跑的
        fresh = os.path.getmtime(f3) >= max(os.path.getmtime(os.path.join(HERE, 'K0_rows_md1.csv')),
                                            os.path.getmtime(os.path.join(HERE, 'check_f3_bound.py')))
        checks.append(('F3 上界：`m ≤ e·j` 0 违例 + 流重建逐位对得上',
                       len(num) == 2 and stream_ok and b3_zero and b2_fires and fresh,
                       '表 %d 行；流自校验 %s；B3 违例 %s；旧界 m≤sz 违例 %s；报告比 K0 数据/脚本旧=%s' % (
                           len(num), 'OK' if stream_ok else '不符', [c[3] for c in num],
                           [c[2] for c in num], '否' if fresh else '是')))
    else:
        checks.append(('F3 上界：`m ≤ e·j` 0 违例 + 流重建逐位对得上', False,
                       'F3_BOUND_CHECK.md 不存在 ⇒ 跑 check_f3_bound.py'))

    # 12 假精度（外部审计 P-11）：确定式解（EOQ 的 q/cost、报童的 q）在种子上给同一个数，
    #     `n_trials_task = 题数 × 10` 是"同一个数抄 10 遍"，按它算 Wilson 就是把 6 个独立观测
    #     吹成 60 个。这里要求：要么这格标了 `R0_*` 且 `n_trials_task == n_tasks`，
    #     要么它的读数**确实有变异**。合成副本可用 `SC_TABLE_TAU_V2.CSV` 负验。
    #     ⚠ 判"是不是同一个数"要用 `n_uniq_trials`（底层唯一值数），**不能**用打印过的 `max_stat`：
    #        22:5x 那次 `md1/J3a`（60 个互不相同的值，2.5e-7~4.25e-6）被 `%.5f` 显示成 0.00000，
    #        于是这条闸红在一条合法格上——闸红在错的地方，跟不响一样是半个闸。
    try:
        tau2 = csv_rows(data('table_tau_v2.csv', 'TAU'))
        r0_bad, fake = [], []
        for r in tau2:
            const = str(r.get('n_uniq_trials', '1')) == '1'
            is_r0 = r['rule'].startswith('R0')
            if is_r0 and not (const and int(r['n_trials_task']) == int(r['n_tasks'])
                              and ('DETERMINISTIC' in (r.get('note') or '')
                                   or 'VACUOUS' in (r.get('note') or ''))):
                r0_bad.append((r['template'], r['statistic'], r['n_trials_task'], r['n_tasks']))
            if const and not is_r0 and int(r['n_trials_task']) == \
                    int(r['n_tasks']) * int(r['budget_seeds']):
                fake.append((r['template'], r['statistic'], r['rule'], r['wilson_hi_task']))
        checks.append(('确定式解不许按"题×种子"算 Wilson（P-11）', not r0_bad and not fake,
                       'R0 格 %d；R0 标记不一致 %s；恒为同一个数却按"题数×%d 种子"当独立试验算上界 %s' % (
                           sum(1 for r in tau2 if r['rule'].startswith('R0')),
                           r0_bad[:3] or '无', int(tau2[0]['budget_seeds']), fake[:3] or '无')))
    except Exception as e:                                   # noqa: BLE001
        checks.append(('确定式解不许按"题×种子"算 Wilson（P-11）', False, repr(e)[:120]))

    # 14 腿 B 开跑前置：每一道有忙度真值的题，口径必须已经写进契约（题面可指认），
    #    否则"每台利用率写对了的正确模型"会在 mmcK 上挨 9–68% 的相对偏差 —— 那正是论文要抓的错型族，
    #    假阳就是这么造出来的（P-05）。检查脚本自带违规清单。
    rc14, msg14 = sh(HERE, ['check_busy_def_text.py'])
    checks.append(('忙度口径有题面载体（腿 B 前置）', rc14 == 0, msg14[:150]))

    # 15 标签两份权威必须逐格相等（`mutants.jsonl` 产物 vs `simcore.CATALOG` 源头）。
    #    做成闸的理由是 10-17 那次：E35 的改判只写进了产物，源头没改（改判脚本的正则跨不过
    #    `short='…(年→日)'` 里的右括号，匹配失败只 print 不 assert，退出码还是 0）。
    #    当天所有表读的都是产物 ⇒ 数没错，但谁重跑一次 `make_mutants.py gen` 就会把
    #    E35 盖回 benign，良性分母 68→74、可检分母 186→180，**而且不报错**。
    rc15, msg15 = sh(HERE, ['check_label_authority.py'])
    checks.append(('标签双权威一致（CATALOG ≡ mutants.jsonl）', rc15 == 0, msg15[:150]))

    # 16 J0 单位锚：正向对照（诚实件 / 诚实换单位的 E28 不许响）+ 三个负样本（谎报
    #    runtime_units / 生词 time_unit / 率与计数矛盾必须响在指定那条腿上）+ NA 语义（缺字段不误伤）。
    #    这条同时是"自愈门柱已关"的验收：生词 time_unit 必须让 J2a/J3a 一起变 NA，
    #    而不是拿默认小时算出一个数冒充通过。脚本会实跑 2 次工件（与 τ* 同口径），约 2 分钟。
    rc16, msg16 = sh(HERE, ['check_j0_anchor_gates.py'])
    j0rep = data('J0_ANCHOR_GATES.md')
    n_fail_row = 0
    if os.path.exists(j0rep):
        n_fail_row = sum(1 for l in io.open(j0rep, encoding='utf-8') if '| FAIL' in l)
    else:
        rc16 = 1
    checks.append(('J0 口径自洽（四腿含 J0e 外部锚）：诚实/真良性件不响 + 谎报各响在指定腿 + NA 不误伤',
                   rc16 == 0 and n_fail_row == 0,
                   '%s；报告里 FAIL 行 %d' % (msg16[:90], n_fail_row)))

    # 17 空判据不许当独立证据（第四轮 R4 的后半句：10-17 我只做到"能在 `rule` 列标记"，
    #    汇总器根本不按 `rule` 过滤 ⇒ 能标记 ≠ 能剔除）。
    #    要求：主表汇总里必须现算印出"独立证据格 N + 空判据格 M"，且 M>0、τ 表里标空的格与 M 同源。
    summ = data('MUTANT_SUMMARY_v2.md')
    ok17, msg17 = False, 'MUTANT_SUMMARY_v2.md 不存在'
    if os.path.exists(summ):
        line = [l for l in io.open(summ, encoding='utf-8') if '独立证据格' in l]
        nums = re.findall(r'\*\*独立证据格 (\d+)\*\*.*?\*\*空判据格 (\d+)\*\*', line[0]) if line else []
        tau2b = csv_rows(data('table_tau_v2.csv', 'TAU'))
        n_vac_tau = sum(1 for r in tau2b if str(r.get('rule') or '').startswith('R0_VACUOUS_INTERNAL'))
        if nums:
            ev, vc = int(nums[0][0]), int(nums[0][1])
            ok17 = ev > 0 and vc > 0 and n_vac_tau > 0
            msg17 = '独立证据格 %d、空判据格 %d；τ 表里标 R0_VACUOUS_INTERNAL 的格 %d 个' % (ev, vc, n_vac_tau)
        else:
            msg17 = '汇总里找不到"独立证据格/空判据格"这一句 ⇒ 剔除没落地（报告行 %d 条）' % len(line)
    checks.append(('空判据不进"独立判据"计数（R0_VACUOUS 要能剔除）', ok17, msg17[:150]))

    # 18 参照件权威唯一（#42 的落地）。根因不是"有人改坏了表"，是**权威声明与实际出口不一致**：
    #    `criteria.py` 顶部曾写"阈值只能在 calib_ref 的参照件上标定"，而现行链条读 `artifacts/`，
    #    10-18 晚我照那句去复算 J0 就探到了历史代（`runtime_units` 是计数），当场发出一条
    #    "stage1 表不可复现"的假警报。主表一格未动，但话已发出 ⇒ 这种错要落成闸，不能只改注释。
    art_src = {}
    for src in ('run_p0_crosscheck.py', 'legB_grade.py'):
        sp = data(src)
        m = re.search(r"^ART(?:_DIR)? *= *os\.path\.join\(HERE, *'([^']+)'",
                      io.open(sp, encoding='utf-8').read(), re.M) if os.path.exists(sp) else None
        art_src[src] = m.group(1) if m else None
    same_art = set(art_src.values()) == set(['artifacts'])
    undecl = undeclared_ref_dirs(HERE)
    # 负样本：临时根里造一个未声明的参照件目录，必须被抓出来（不咬人的闸 = 半个闸）
    tmp = __import__('tempfile').mkdtemp(prefix='refdup_neg_')
    try:
        os.makedirs(os.path.join(tmp, 'oldrefs'))
        for i in range(6):
            with open(os.path.join(tmp, 'oldrefs', 'mm1-%02d__REF.py' % i), 'w',
                      encoding='utf-8') as fh:
                fh.write('x = 1\n')
        neg = undeclared_ref_dirs(tmp)
    finally:
        __import__('shutil').rmtree(tmp, ignore_errors=True)
    ok18 = same_art and not undecl and len(neg) == 1
    checks.append(('参照件权威唯一（非 artifacts 的代必须声明；含负样本）', ok18,
                   '两个出口指向=%s ｜仓内未声明=%s ｜负样本抓到 %d/1' % (
                       list(art_src.values()), undecl or '无', len(neg))))

    n_fail = 0
    emit('# 仪器自检（可执行版）  %s' % __import__('time').strftime('%Y-%m-%d %H:%M'))
    for name, ok, msg in checks:
        n_fail += (0 if ok else 1)
        emit('%-34s %-6s %s' % (name, 'PASS' if ok else 'FAIL', msg))
    out = os.environ.get('SC_SELFCHECK_OUT') or os.path.join(HERE, 'SELFCHECK.md')
    with io.open(out, 'w', encoding='utf-8') as f:
        # **条数写在标题行里、由 `len(checks)` 现算**（第四轮 R4-3：盘上同时流传过
        # 11/13/14/16 四种说法，负样本账还同格并存"8 条"与"10/10" ⇒ "自检 N 项全绿"这句话
        # 没有载体）。标题带数，引用的人就必须对得上这份文件。
        f.write('# 仪器自检（可执行版）— 共 %d 项，PASS %d，FAIL %d\n\n' % (
            len(checks), len(checks) - n_fail, n_fail))
        for name, ok, msg in checks:
            f.write('- %s **%s** — %s\n' % ('PASS' if ok else 'FAIL', name, msg))
    print('\n合计 %d 项，失败 %d 项；已写 %s' % (len(checks), n_fail, out))
    return n_fail


if __name__ == '__main__':
    sys.exit(main())
