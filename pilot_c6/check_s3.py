"""校验器：把预实验报告 §3 主表里能解析出的配对数，与 pilot2_results.jsonl 对账。

与 gen_s3_table.py 的关系：**它不共享那张行规格表**，自己按标签里的关键词认行
（LCFS/SIRO/cap=20/20→17/重复累加/指数→定长…），所以两张表如果指错了对象会被抓住。
判据：报告值必须等于 jsonl 值四舍五入到报告位数；解析不到数、或对不上，都算 FAIL。

**范围要说清楚**（外部审计 F-7 的后半条）：只扫 §3 主表那一段（`| 变异（注入的错误） |` 到 `### 3.1`）。
报告 §6（预算 E）里也有一行"排队规则 FCFS→LCFS"，但那是**另一次实验**（12 配对种子 / horizon 80000），
数字本来就不该与 §3 相同 ⇒ 本校验器故意不比它，改由 `check_s6.py` 管（没有就是没管，别假称管了）。

编码：Windows 控制台默认 cp936，`⚠`/`✓` 这类符号会让 print 直接崩（审计 F-9），
所以本文件的警告一律写 `[WARN]`；`selfcheck_all.py` 给子进程显式设 `PYTHONIOENCODING=utf-8`。
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, '..', 'pre_experiment_report_C6_2026-10-16.md')
RES = os.path.join(HERE, 'pilot2_results.jsonl')

# (标签里必须出现的词, 不能出现的词, scene, mut)
PATTERNS = [
    (('FCFS→LCFS',), ('SIRO',), 'mm1_r80', 'disc_lcfs'),
    (('FCFS→SIRO',), (), 'mm1_r80', 'disc_siro'),
    (('冗余无用状态',), (), 'mm1_r80', 'noop_extra_state'),
    (('单位换算',), (), 'mm1_r80', 'unit_scale_both'),
    (('重复累加',), (), 'mm1_r80', 'dep_double_count'),
    (('指数→定长',), (), 'mm1_r80', 'svc_determ'),
    (('漏写容量上限',), (), 'mm1K_cap20', 'cap_omitted'),
    (('容量上限 20→17',), ('漏写',), 'mm1K_cap20', 'cap_minus3'),
]
NUM = re.compile(r'([+−-]\d+(?:\.\d+)?)\s*%\s*±\s*(\d+(?:\.\d+)?)\s*%')
NUM5 = re.compile(r'([+−-]\d\.\d{5})\s*±\s*(\d\.\d{5})')
# 报告里**故意**留成文字（"报警/同量级/—"）的格：键 = (scene, mut, 列号)。
# 空集合是有意为之——跑一次让它把当前占位格报出来，逐条决定"补数"还是"进名单并写理由"。
ALLOWED_SKIP = set()


def val(s):
    return float(s.replace('−', '-'))


def main():
    recs = {(r['scene'], r['mut']): r for r in
            (json.loads(l) for l in io.open(RES, encoding='utf-8') if l.strip())}
    txt = io.open(REPORT, encoding='utf-8').read()
    i = txt.index('| 变异（注入的错误） |')
    j = txt.index('### 3.1', i)
    rows = {}
    dup_lines = []
    for line in txt[i:j].splitlines():
        if not line.startswith('|') or line.count('|') < 6:
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        label = cells[0]
        for must, mustnot, sc, mut in PATTERNS:
            if all(w in label for w in must) and not any(w in label for w in mustnot):
                # ⚠ 原来这里无条件 `rows[key] = cells`：同名行后写覆盖前写，于是"表里其实有两行
                # 都算这条模式"会被静默吞掉（审计 P-21②）。现在撞键就记一笔。
                if (sc, mut) in rows and rows[(sc, mut)] != cells:
                    dup_lines.append((sc, mut, rows[(sc, mut)][0], label))
                rows[(sc, mut)] = cells
                break
    bad = []
    skips = []
    for key, cells in sorted(rows.items()):
        if key not in recs:
            bad.append('%s/%s 在 jsonl 里没有这行' % key)
            continue
        r = recs[key]
        for idx, vk, hk, nd, pct in ((2, 'dL_rel', 'dL_rel_hw', 3, True),
                                     (3, 'dW_rel', 'dW_rel_hw', 3, True),
                                     (4, 'dCons', 'dCons_hw', 5, False)):
            pat = NUM if pct else NUM5
            m = pat.search(cells[idx])
            if not m:
                # 占位文字（"同量级/—/报警"）是**故意的**，但"故意留空"和"解析不出来"必须分得开：
                # 原来只 n_skip += 1 再 print，`return 0 if not bad` 里根本没有它 ⇒
                # 把整列换成"报警 ± 同量级"照样 PASS（外部审计 F-7）。
                # 现在：跳过要落进白名单（题到列），名单外的一律算不一致；`missing` 同理。
                if '同量级' in cells[idx] or '—' == cells[idx] or '报警' in cells[idx]:
                    skips.append((key[0], key[1], idx, cells[idx]))
                    continue
                bad.append('%s/%s 第%d列解析不到数：%r' % (key[0], key[1], idx, cells[idx]))
                continue
            gv, gh = val(m.group(1)), val(m.group(2))
            ev, eh = (100 * r[vk], 100 * r[hk]) if pct else (r[vk], r[hk])
            if round(ev, nd) != round(gv, nd) or round(eh, nd) != round(gh, nd):
                bad.append('%s/%s 第%d列 报告 %+.5f±%.5f vs jsonl %+.5f±%.5f' % (
                    key[0], key[1], idx, gv, gh, ev, eh))
    missing = [str(k) for k in recs if k not in rows and k[1] not in ('no_warmout', 'c_minus1', 'c_frozen1',
                                                                      'arr_determ', 'batch2')]
    # 分母锁：模式表声明了几行，报告里就必须解析出几行；少一行就说明有条模式没匹配到（或被改名）。
    if len(rows) != len(PATTERNS):
        bad.append('分母锁：PATTERNS 声明 %d 行，报告只解析到 %d 行 ⇒ 缺 %s' % (
            len(PATTERNS), len(rows),
            ','.join('%s/%s' % p[2:] for p in PATTERNS if (p[2], p[3]) not in rows)))
    for sc, mut, prev, now in dup_lines:
        bad.append('同名两行撞进同一格 %s/%s：先匹配到 %r，后又匹配到 %r ⇒ 表里有重复行' % (
            sc, mut, prev, now))
    # 占位必须落白名单：名单外的"解析不到数"一律算 FAIL（审计 F-7：原来 n_skip 只 print，
    # 把整列换成 报警/同量级 照样 rc=0）。
    for s in skips:
        if (s[0], s[1], s[2]) not in ALLOWED_SKIP:
            bad.append('占位跳过没在白名单里：%s/%s 第 %d 列 = %r ⇒ 要么补数，要么写进 ALLOWED_SKIP 并说明理由'
                       % (s[0], s[1], s[2], s[3]))
    print('解析到 %d 行 / jsonl 里该进表的 %d 格；不一致 %d 处；故意占位跳过 %d 格（白名单 %d 格）' % (
        len(rows), len(recs), len(bad), len(skips), len(ALLOWED_SKIP)))
    for b in bad:
        print('  FAIL ' + b)
    for s in skips:
        print('  占位 %s/%s 第%d列 = %r' % (s[0], s[1], s[2], s[3]))
    if missing:
        print('  [WARN] jsonl 有但 §3 主表里没有对应行（本校验器只扫 §3 那一段）：%s' % missing)
    print('PASS' if not bad else 'FAIL')
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
