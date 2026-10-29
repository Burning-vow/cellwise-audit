"""把 E35 的"改判"从脚本字典写回**标签源头**（`simcore.py` 的 CATALOG 与 `mutants.jsonl`）。

为什么现在才做：分片进程在 import `simcore.py`，改它会让正在跑的件崩（今天崩过三次）。
本脚本必须在 `run_mutant_matrix` / `check_benign` 全部停下之后跑。

改三处，并逐处断言"只改了该改的字段"：
  1) `mutants.jsonl`：6 条 E35 记录的 `expected` 由 benign → detectable，并写 `relabel_reason`（带实测）；
  2) `simcore.py`：CATALOG['E35']['expected'] 同步 ⇒ 以后重新生成 `mutants.jsonl` 不会再退回 benign；
  3) 6 个工件薄壳头部那行 `expected=...`（只是注释文字，但后续 AI 会读它）。
最后把 `check_benign.py` 的本地字典 `RELABELED` 清空，并加断言：
**`mutants.jsonl` 里标 benign 的集合，必须等于 `BENIGN_PROOF.csv` 的成员集合** —— 这就是防漂移的那道闸。
"""
import io
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MUTJ = os.path.join(HERE, 'mutants.jsonl')
SIMCORE = os.path.join(HERE, 'simcore.py')
BENIGN = os.path.join(HERE, 'check_benign.py')
ART = os.path.join(HERE, 'artifacts')
BAK = os.path.join(HERE, '_archive_superseded', 'label_fix_backup')
REASON = ('10-17 实测：同一件在 J1·q 上 rel=0.0000 不点火、在 J1·cost 上 rel=0.9973 点火'
          '（元/日 当 元/年 上报，差 365 倍）⇒ 建模不变但报单口径错，不能当良性对照')


def running_jobs():
    """先确认没有分片在跑：改 simcore 会让它们崩。用产物是否还在长大来判断。

    ⚠ 2026-10-17 补：原来只盯 `MUTANT_MATRIX_R10.shard*.csv` + `BENIGN_PROOF.csv`，
    而 `run_recal64.py` 也经 `criteria.run_artifact` 起 `artifacts/*.py` 子进程、同样 import `simcore`
    ⇒ 那种时候这道闸会**放行**，正好把"改内核让在跑的件崩"放回原路。现在把
    标定分片 `_recal_shard*.jsonl`、`P0_CROSSCHECK.csv`、以及 R10b 那一代分片一起纳入监视。
    """
    import glob
    import time
    pats = ['MUTANT_MATRIX_R10.shard*.csv', 'MUTANT_MATRIX_R10b.shard*.csv',
            '_recal_shard*.jsonl', 'BENIGN_PROOF.csv', 'P0_CROSSCHECK.csv']
    files = sorted({os.path.abspath(f) for p in pats for f in glob.glob(os.path.join(HERE, p))})
    if not files:
        raise SystemExit('监视清单为空 ⇒ 这道闸没在保护任何东西，先修清单')
    a = [(f, os.path.getsize(f) if os.path.exists(f) else -1) for f in files]
    time.sleep(20)
    b = {f: (os.path.getsize(f) if os.path.exists(f) else -1) for f in files}
    grew = [os.path.basename(f) for f, s in a if b[f] != s]
    if grew:
        print('[在跑] 这些产物还在长大：%s' % ','.join(grew))
    return bool(grew)


def main():
    if running_jobs():
        raise SystemExit('还有分片在写产物 ⇒ 不许改 simcore.py（会让在跑的件崩）。等它跑完再来。')
    os.makedirs(BAK, exist_ok=True)
    for f in (MUTJ, SIMCORE, BENIGN):
        if os.path.exists(f):
            shutil.copy2(f, os.path.join(BAK, os.path.basename(f)))

    # 1) mutants.jsonl
    recs = [json.loads(l) for l in io.open(MUTJ, encoding='utf-8') if l.strip()]
    n = 0
    for r in recs:
        if r['error_type'] == 'E35':
            assert r['expected'] in ('benign', 'detectable'), r
            if r['expected'] != 'detectable':
                r['expected'] = 'detectable'
                r['relabel_reason'] = REASON
                n += 1
            else:
                r.setdefault('relabel_reason', REASON)
    print('mutants.jsonl 改判 %d 条 E35（期望 6）' % n)
    assert n in (0, 6), 'E35 条数不对：%d' % n
    with io.open(MUTJ, 'w', encoding='utf-8') as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    # 2) simcore CATALOG
    # ⚠ 10-17 这一步**静默没做成**：原来的正则用 `[^)]*` 跨不过 `short='…(年→日)'` 里的那个右括号，
    #    于是匹配失败走了 else 分支、只 print 了一句"检查"就继续，脚本照样退出 0。
    #    后果：`make_mutants.py` 重新生成 `mutants.jsonl` 时会把 E35 退回 benign ⇒ 分母换一套数。
    #    现在：正则改成非贪婪跨括号，且**改完必须回读断言**，不再允许"匹配不到就当没事发生"。
    s = io.open(SIMCORE, encoding='utf-8').read()
    m = re.search(r"'E35': dict\(family='estimation',.*?expected='(benign|detectable)'", s, re.S)
    assert m, "没在 simcore.py 里定位到 CATALOG['E35'] ⇒ 结构变了，手工核对第 193 行附近"
    if m.group(1) == 'benign':
        s = s[:m.start()] + m.group(0).replace("expected='benign'", "expected='detectable'") + s[m.end():]
        io.open(SIMCORE, 'w', encoding='utf-8').write(s)
        print('CATALOG[E35].expected → detectable')
    else:
        print('CATALOG[E35] 已是 detectable，本步跳过')
    import simcore as _SC
    assert _SC.CATALOG['E35']['expected'] == 'detectable', \
        '写回后回读仍是 %s ⇒ 标签源头没闭环（第 1 步改了 mutants.jsonl，源头会把它盖回去）' \
        % _SC.CATALOG['E35']['expected']

    # 3) 工件头部注释
    changed = []
    for fn in sorted(os.listdir(ART)):
        if not fn.endswith('__e35.py'):
            continue
        p = os.path.join(ART, fn)
        t = io.open(p, encoding='utf-8').read()
        if 'expected=benign' in t:
            t = t.replace('expected=benign', 'expected=detectable')
            io.open(p, 'w', encoding='utf-8').write(t)
            changed.append(fn)
    print('工件头部改判 %d 个：%s' % (len(changed), changed))

    # 4) check_benign 的本地字典清空。
    #    ⚠ 原来这一步还要往 check_benign 里塞一个 `check_label_consistency()` 函数，
    #    但没人调用它 = 死代码；而且"mutants 的 benign 集合 ≡ BENIGN_PROOF 成员集合"这条断言
    #    **已经做成闸**了（`selfcheck_all.py` 第 6 项，且它比这个函数多了"只自证不在标签里"的反方向差集）。
    #    所以这里只清本地字典，并在文件头留一句指向那道闸。
    b = io.open(BENIGN, encoding='utf-8').read()
    if "RELABELED = {'E35': 'detectable', 'E28': 'benign'}" in b:
        b = b.replace("RELABELED = {'E35': 'detectable', 'E28': 'benign'}",
                      "RELABELED = {}   # 改判已写回标签源头（mutants.jsonl + simcore.CATALOG）；"
                      "成员集合一致性由 selfcheck_all 第 6 项断言，不在这里另立一份")
        io.open(BENIGN, 'w', encoding='utf-8').write(b)
        print('check_benign 的 RELABELED 已清空（集合断言在 selfcheck 第 6 项，不重复实现）')
    else:
        print('RELABELED 不是预期写法，检查 check_benign.py 顶部')

    # 复核：标签现在两处必须一致（**断言，不是 print** —— print 过的地方就会有人不当回事）
    ms = [json.loads(l) for l in io.open(MUTJ, encoding='utf-8') if l.strip()]
    e35 = sorted({r['expected'] for r in ms if r['error_type'] == 'E35'})
    assert e35 == ['detectable'], 'mutants.jsonl 里 E35 = %s' % e35
    assert _SC.CATALOG['E35']['expected'] == 'detectable', 'CATALOG 里 E35 还是 benign'
    print('复核：E35 的 expected =', e35, '；CATALOG[E35] =', _SC.CATALOG['E35']['expected'])
    print('备份在', BAK)


if __name__ == '__main__':
    sys.exit(main())
