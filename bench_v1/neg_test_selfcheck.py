"""自检里**每一条闸，哪几条从没被坏样本咬过**——这个脚本就是那张账。
（闸的条数不在这里写死：`NEGATIVE_TESTS.md` 由本脚本现算，加一条闸就加一个 case，账自动跟着走。）

为什么要有它（他问"如何才能判断是否有其他错误"的可操作答案）：
一条不响的断言等于没有断言。上一轮已经抓到过三个"半个门禁"：
第 5 项只数 FAIL 不判 FAIL、第 6 项分母是自报行数、第 7 项在报告里查字面量 `58/58`。
所以"全绿"本身不是证据，**"每条闸都红过一次、且红在该红的地方"才是**。

做法：给每一条闸造一个最小坏样本（temp 里的合成副本，交付物一个字节不动），
用 `SC_*` 那些口子喂进去，跑一次真自检，要求**指定那一项 FAIL**（不是"整体 FAIL 就行"——
那样分不清是哪条闸响的）。结果写 `NEGATIVE_TESTS.md`，没负样本的闸要显式列成"半个门禁"。
"""
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
OUT = os.path.join(HERE, 'NEGATIVE_TESTS.md')
P6 = os.path.join(HERE, '..', 'pilot_c6')


def rd(p):
    return io.open(p, encoding='utf-8').read()


def wr(d, name, text):
    p = os.path.join(d, name)
    io.open(p, 'w', encoding='utf-8', newline='').write(text)
    return p


def case_g3(d):
    rows = rd(os.path.join(HERE, 'RECAL_CURRENCY.csv')).splitlines(True)
    rows[1] = rows[1].replace(',IDENTICAL,', ',DRIFT,')
    return {'SC_RECAL_CURRENCY.csv': wr(d, 'neg_currency.csv', ''.join(rows))}, '标定残差 vs 当前引擎'


def case_g4(d):
    src = rd(os.path.join(HERE, 'run_p0_crosscheck.py'))
    line = [l for l in src.splitlines() if l.startswith('SEEDS =')][0]
    return {'SC_RUN_P0': wr(d, 'neg_run_p0.py',
                            src.replace(line, 'SEEDS = 5   # 故意与 tau_basis_seeds 不一致'))}, \
        'τ* 预算 == 门禁预算'


def case_g5(d):
    rows = list(csv.DictReader(io.open(os.path.join(HERE, 'P0_CROSSCHECK.csv'), encoding='utf-8')))
    rows[0]['gate'] = 'FAIL'
    p = os.path.join(d, 'neg_p0.csv')
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        [w.writerow(r) for r in rows]
    return {'SC_P0': p}, 'stage1 门禁'


def case_g6(d):
    rows = list(csv.DictReader(io.open(os.path.join(HERE, 'BENIGN_PROOF.csv'), encoding='utf-8')))
    keep = rows[:-1]                                   # 删掉一件自证通过的 ⇒ 集合等式必须响
    p = os.path.join(d, 'neg_benign.csv')
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        [w.writerow(r) for r in keep]
    return {'SC_BENIGN_PROOF.csv': p}, '良性标签单一权威'


def case_g7(d):
    lines = [json.loads(l) for l in io.open(os.path.join(P6, 'pilot_results.jsonl'), encoding='utf-8')
             if l.strip()]
    lines[0]['rel_W'] = float(lines[0]['rel_W']) + 1e-6       # 只动一个读数
    p = os.path.join(d, 'neg_pilot_new.jsonl')
    with io.open(p, 'w', encoding='utf-8') as f:
        [f.write(json.dumps(r, ensure_ascii=False) + '\n') for r in lines]
    return {'SC_PILOT_NEW': p}, '受控 A/B'


def case_g11(d):
    txt = rd(os.path.join(HERE, 'F3_BOUND_CHECK.md'))
    lines = [l for l in txt.splitlines() if l.startswith('| lcfs')]
    bad = lines[0].replace('| 0 | 1,2,3', '| 3 | 1,2,3')       # B3 违例从 0 改成 3
    assert bad != lines[0], 'F3 报告格式变了，先修这个负样本'
    return {'SC_F3': wr(d, 'neg_f3.md', txt.replace(lines[0], bad))}, 'F3 上界'


def case_g12(d):
    rows = list(csv.DictReader(io.open(os.path.join(HERE, 'table_tau_v2.csv'), encoding='utf-8')))
    hit = [r for r in rows if r['rule'].startswith('R0')]
    assert hit, '表里没有 R0 格 ⇒ 这条闸没东西可咬（先确认 build_tables_v2 已在新代码上重跑）'
    hit[0]['rule'] = 'R1'
    hit[0]['n_trials_task'] = str(int(hit[0]['n_tasks']) * 10)      # 退回"题×种子"那种假精度
    hit[0]['note'] = ''
    # 新口径下判定看 `n_uniq_trials`（恒为同一个数），所以坏样本要把它设成 1；
    # 只改 max_stat 是无效的——那正是 22:5x 误报的根源。
    if 'n_uniq_trials' in hit[0]:
        hit[0]['n_uniq_trials'] = '1'
    p = os.path.join(d, 'neg_tau.csv')
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        [w.writerow(r) for r in rows]
    return {'SC_TAU': p, 'SC_TAU_CSV': p}, '确定式解不许按'


def case_g10(d):
    rows = list(csv.DictReader(io.open(os.path.join(HERE, 'table_tau_v2.csv'), encoding='utf-8')))
    tpl = sorted({r['template'] for r in rows})[0]
    keep = [r for r in rows if r['template'] != tpl]                # 抽掉一个模板的全部 τ* 行
    p = os.path.join(d, 'neg_tau_notpl.csv')
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        [w.writerow(r) for r in keep]
    return {'SC_TAU_CSV': p}, '每模板都有带 τ 星的观测量'


def case_g14(d):
    """腿 B 前置闸的坏样本：一道有忙度真值的题被抽掉 `busy_def` ⇒ 必须响。"""
    keep = []
    n = 0
    for l in io.open(os.path.join(HERE, 'tasks.jsonl'), encoding='utf-8'):
        if not l.strip():
            continue
        t = json.loads(l)
        if t.get('busy_def') and n == 0 and (t.get('truth_raw') or {}).get('busy_frac') is not None:
            t['busy_def'] = None          # 模拟"题集没重生成就改了内核"
            n += 1
        keep.append(json.dumps(t, ensure_ascii=False))
    assert n == 1, '没找到可抽的题 ⇒ 这道闸没东西可咬'
    nl = chr(10)                     # 不在源码里写转义换行（heredoc 会把 \\n 写坏，今天踩过）
    return {'SC_TASKS_JSONL': wr(d, 'neg_tasks.jsonl', nl.join(keep) + nl)}, '忙度口径有题面载体'


def case_g3b(d):
    """半截 currency 表（25 行、mtime 最新）也必须 FAIL —— 00:0x 那次它骗过了第 3 项。"""
    rows = rd(os.path.join(HERE, 'RECAL_CURRENCY.csv')).splitlines(True)
    head = [l for l in rows if l.startswith('task_id,')][:1]
    body = [l for l in rows if not l.startswith('task_id,')][:25]
    return {'SC_RECAL_CURRENCY.csv': wr(d, 'neg_currency_short.csv', ''.join(head + body))}, \
        '标定残差 vs 当前引擎'


def case_g15(d):
    """标签双权威的坏样本：把 E35 在**产物副本**里改回 benign（就是 10-17 源头没写回时的那个状态）
    ⇒ 第 15 项必须响在"CATALOG ≠ mutants.jsonl"上。交付物 `mutants.jsonl` 一个字节不动。"""
    out = []
    n = 0
    for l in io.open(os.path.join(HERE, 'mutants.jsonl'), encoding='utf-8'):
        if not l.strip():
            continue
        r = json.loads(l)
        if r['error_type'] == 'E35':
            r['expected'] = 'benign'
            n += 1
        out.append(json.dumps(r, ensure_ascii=False))
    assert n == 6, 'E35 行数是 %d，跟标签账（6 件）不符 ⇒ 坏样本没造对' % n
    nl = chr(10)
    return {'LA_MUTANTS': wr(d, 'neg_mutants.jsonl', nl.join(out) + nl),
            'LA_OUT': os.path.join(d, 'neg_label_authority.md')}, \
        '标签双权威一致（CATALOG ≡ mutants.jsonl）'


def case_g16(d):
    """J0 锚的坏样本 = **一次真回归**，不是手改报告文字。

    把单位解析改回 10-18 之前的行为（认不出来就当小时），在 temp 里跑一遍 J0 验收：
    生词 `time_unit='fortnight'` 那格就不该再有 `unknown_unit`，J2a/J3a 会拿默认小时算出个
    数来冒充通过 ⇒ 验收必须 FAIL ⇒ 第 16 项必须红。
    交付物与 `criteria.py` 都不动：补丁只活在那个临时子进程的内存里。
    """
    rep = os.path.join(d, 'neg_j0_report.md')
    runner = wr(d, 'neg_j0_lenient.py', '\n'.join([
        'import os, sys',
        'HERE = r"%s"' % HERE,
        'sys.path.insert(0, HERE)',
        "os.environ['J0AG_OUT'] = r'%s'" % rep,
        'import criteria as C',
        # 旧行为：词表外的单位 -> 默认 1.0（=小时），于是"撒谎声明单位"白拿一个不换算的通过
        'C._unit_hours_strict = lambda u: C._unit_hours(u, 1.0)',
        'import check_j0_anchor_gates as G',
        'sys.exit(G.main())',
        '']))
    p = subprocess.run([PY, runner], cwd=HERE, capture_output=True,
                       text=True, encoding='utf-8', errors='replace')
    txt = rd(rep) if os.path.exists(rep) else ''
    assert '| FAIL' in txt, ('坏样本自己没坏（rc=%s）⇒ 第 16 项是半个门禁：%s' % (
        p.returncode, (p.stdout or '')[-300:]))
    return {'SC_J0_ANCHOR_GATES.md': rep}, 'J0 口径自洽'


def case_g17(d):
    """空判据剔除那条闸的坏样本：把汇总里"独立证据格 / 空判据格"那句**整行删掉**
    （模拟"只标记不剔除"的旧状态又回来）⇒ 第 17 项必须响在这一项上。"""
    txt = rd(os.path.join(HERE, 'MUTANT_SUMMARY_v2.md'))
    assert '独立证据格' in txt, '当前汇总里没有那句 ⇒ 第 17 项没东西可咬（先重跑 summarize）'
    bad = '\n'.join(l for l in txt.splitlines() if '独立证据格' not in l)
    return {'SC_MUTANT_SUMMARY_v2.md': wr(d, 'neg_summary_novac.md', bad)}, '空判据不进'


def case_g5b(d):
    """追加型脚本被打断后重跑会留**重复键**（同一 题/阶段/观测量/扰动 两次）。
    坏样本：把第一行原样再写一遍 ⇒ 第 5 项必须因为"重复行>0"红。
    （10-18 合盖暂停那次我是手工数出来的，手工数不等于有闸。）"""
    rows = list(csv.DictReader(io.open(os.path.join(HERE, 'P0_CROSSCHECK.csv'), encoding='utf-8')))
    rows.insert(5, dict(rows[0]))              # 复制一行，键完全相同
    p = os.path.join(d, 'neg_p0_dup.csv')
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        [w.writerow(r) for r in rows]
    return {'SC_P0': p}, 'stage1 门禁'


CASES = [('第 3 项', case_g3), ('第 3 项b 半截表', case_g3b), ('第 14 项', case_g14),
         ('第 15 项', case_g15), ('第 16 项', case_g16), ('第 17 项', case_g17),
         ('第 4 项', case_g4), ('第 5 项', case_g5), ('第 5 项b 重复键', case_g5b),
         ('第 6 项', case_g6),
         ('第 7 项', case_g7), ('第 10 项', case_g10), ('第 11 项', case_g11), ('第 12 项', case_g12)]
NO_NEG = [('第 1、2 项（报告对账）', '负样本不在这里造，在 `../pilot_c6/check_pilot_gates.py`：'
                                      'M1 占位文字、M2 删行、M3 换 §3.3 规则文字，三个变异各自要求响在指定的闸上'),
          ('第 6 项后半（良性对照自证闸）', '本脚本第 6 项的坏样本打的是"集合等式"那一半；'
                                      '`verdict != PROVES_BENIGN` 那一半没单独造样本（要真造就得改判据，不划算）'),
          ('第 8 项（busy 两义分开）', '它是**源码子串**断言，只能防"把修好的口径改回去"，'
                                      '不是对读数的判据 ⇒ 按 §17 的规矩不许算成"测过"')]


def run_selfcheck(env, d):
    rep = os.path.join(d, 'SELFCHECK_neg.md')
    e = dict(os.environ, PYTHONIOENCODING='utf-8', SC_SELFCHECK_OUT=rep)
    e.update(env)
    p = subprocess.run([PY, 'selfcheck_all.py'], cwd=HERE, capture_output=True,
                       text=True, encoding='utf-8', errors='replace', env=e)
    lines = io.open(rep, encoding='utf-8').read().splitlines() if os.path.exists(rep) else []
    fails = [l.split('**')[1] for l in lines if l.startswith('- FAIL')]
    return p.returncode, fails, lines


def main():
    d = tempfile.mkdtemp(prefix='negselfcheck_')
    res, detail = [], []
    for tag, fn in CASES:
        env, want = fn(d)
        rc, fails, lines = run_selfcheck(env, d)
        hit = any(want in f for f in fails)
        res.append((tag, want, hit, rc, [f for f in fails if want not in f]))
        print('[%s] 目标=%s 命中=%s rc=%s 其它红项=%s' % (
            tag, want, hit, rc, [f for f in fails if want not in f]), flush=True)
    shutil.rmtree(d, ignore_errors=True)

    L = ['# 自检闸的负样本账（`neg_test_selfcheck.py` 产生）', '',
         '判据：不是"整体 FAIL 就行"，而是**指定的那一项必须红**；红在别处算没命中。', '',
         '| 闸 | 坏样本 | 命中？ | 顺带红的项 |', '|---|---|---|---|']
    for tag, want, hit, rc, other in res:
        L.append('| %s | %s | %s | %s |' % (tag, want, '响' if hit else '**没响**',
                                            ', '.join(other) or '无'))
    n_hit = sum(1 for _, _, h, _, _ in res if h)
    L += ['', '**命中 %d / %d 条**；没有合成负样本的项（照实列，不当"已验"）：' % (n_hit, len(res)), '']
    for t, why in NO_NEG[:3]:
        L.append('- %s —— %s' % (t, why))
    L += ['', '⚠ 这张表不等于"闸都有效"，它只等于"每条闸都真的会红"。',
          '闸的**内容**对不对，仍然只能靠外部复算与独立实现——这条已在 `预注册 §20` 里被证实两次：'
          '第 3 项改成 mtime 新鲜度断言，是因为读旧快照会"永远绿"；第 11 项要求**旧界必须报违例**，'
          '是因为一份不改坏的复核等于没复核。', '']
    txt = '\n'.join(L) + '\n'
    io.open(OUT, 'w', encoding='utf-8').write(txt)
    sys.stdout.buffer.write(txt.encode('utf-8'))
    return 0 if n_hit == len(res) else 1


if __name__ == '__main__':
    sys.exit(main())
