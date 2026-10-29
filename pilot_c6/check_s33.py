"""校验器：把 `预实验报告 §3.3` 那张 2×2 表里的 ΔL / ΔW 数字回读出来，和 pilot4_results.jsonl 对账。

为什么要有这个文件：ΔL 列刚被我用 Edit 手改过一遍。**手改表格正是"生成式报告里不许有手写判断句"
这条规则的同族风险**——改动对不对，不能靠我自己说"我照着表改的"。
本校验器与报告文字**机制独立**：它只认 jsonl 里的浮点数，不认报告。

判据：报告里每个数都必须在 jsonl 对应量的"四舍五入到报告位数"之后相等。
任何一条不等就报 FAIL 并打印两边，不静默。
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
REPORT = os.path.join(ROOT, 'pre_experiment_report_C6_2026-10-16.md')
RES = os.path.join(HERE, 'pilot4_results.jsonl')

# 报告表格的行序 = jsonl 的写入序（pilot4.main 的循环顺序：场景外层、规则 lcfs/siro/spt 内层）
ORDER = [('mm1_exp', 'lcfs'), ('mm1_exp', 'siro'), ('mm1_exp', 'spt'),
         ('mm1_det', 'lcfs'), ('mm1_det', 'siro'), ('mm1_det', 'spt'),
         ('mmc2_exp', 'lcfs'), ('mmc2_exp', 'siro'), ('mmc2_exp', 'spt')]
RULE_RE = re.compile(r'^\|\s*(M/M/1|M/D/1|M/M/2)[^|]*\|\s*([^|]+?)\s*\|')


def parse_report_rows(txt):
    """返回 [(规则标签, (ΔL均值,ΔL半宽), (ΔW均值,ΔW半宽), 原始行), ...]，单位=百分数。

    两个坑：
      1) 不硬编码列序 —— 表里只有 ΔL/ΔW 写成 "x% ± y%"，用"含 ± 的单元格"定位比数下标稳；
      2) 必须先把范围切到 §3.3，否则 §8 那张"L 修前/修后"表也含 "M/M/1"，会被当成 2×2 的行。
    """
    i = txt.index('### 3.3')
    j = txt.index('## 4.', i)
    rows = []
    for line in txt[i:j].splitlines():
        m = RULE_RE.match(line)
        if not m:
            continue
        cells = [c.strip().replace('−', '-') for c in line.strip().strip('|').split('|')]
        pm = [c for c in cells if '±' in c]
        if len(pm) < 2:
            rows.append((m.group(2), [None, None], [None, None], line))     # 交给主循环报 FAIL
            continue

        def two(s):
            v = re.findall(r'([+-]?\d+(?:\.\d+)?)\s*%', s)
            return [(float(v[0]) if len(v) > 0 else None), (float(v[1]) if len(v) > 1 else None)]
        rows.append((m.group(2), two(pm[0]), two(pm[1]), line))
    return rows


def main():
    txt = io.open(REPORT, encoding='utf-8').read()
    rows = parse_report_rows(txt)
    recs = {(r['scene'], r['disc']): r for r in
            (json.loads(l) for l in io.open(RES, encoding='utf-8') if l.strip())}
    if len(rows) != len(ORDER):
        print('FAIL 报告里解析到 %d 行，期望 %d 行 —— 先修解析器，别谈数字' % (len(rows), len(ORDER)))
        for r in rows:
            print('   解析行:', r[0])
        return 1
    bad = 0

    def label_rule(txt):
        """从报告那一行的规则列文字里认规则。⚠ 这条断言是 2026-10-17 补的（审计 P-21）：
        原来本校验器**只按位置**把报告行与 jsonl 的 ORDER 配对，规则列不参与判定 ⇒
        把人家的规则文字与数值对调，两份都还在、数也各归各，而校验器照样 PASS。"""
        t = txt.upper()
        hits = [v for k, v in (('LCFS', 'lcfs'), ('SIRO', 'siro'), ('SPT', 'spt')) if k in t]
        return hits[0] if len(hits) == 1 else None

    for (rule_label, dl, dw, line), key in zip(rows, ORDER):
        got_rule = label_rule(rule_label)
        if got_rule != key[1]:
            print('FAIL 第 %d 行的规则文字与 jsonl 的键不一致：报告=%r 认出=%r 但按位置配给了 %s/%s'
                  ' ⇒ 表里的行被换过序（或解析器抓错了行）' % (
                      rows.index((rule_label, dl, dw, line)) + 1,
                      rule_label, got_rule, key[0], key[1]))
            bad += 1
            continue
        r = recs[key]
        exp = [(100 * r['dL_rel'], 100 * r['dL_rel_hw']), (100 * r['dW_rel'], 100 * r['dW_rel_hw'])]
        got = [dl, dw]
        for name, e, g in (('dL', exp[0], got[0]), ('dW', exp[1], got[1])):
            for tag, ev, gv in (('mean', e[0], g[0]), ('hw', e[1], g[1])):
                if gv is None:
                    print('FAIL %s/%s %s.%s 报告里没解析出数：%s' % (key[0], key[1], name, tag, line[:70]))
                    bad += 1
                elif round(ev, 3) != round(gv, 3):
                    print('FAIL %s/%s %s.%s 报告=%.3f%% jsonl=%.3f%% 差=%.3g' % (
                        key[0], key[1], name, tag, gv, ev, gv - ev))
                    bad += 1
    print('%s  §3.3 的 9 行 × (ΔL,ΔW) × (均值,半宽) = 36 个数，不一致 %d 个' % (
        'PASS' if bad == 0 else 'FAIL', bad))
    print('    规则标签核对：%s' % ([r[0] for r in rows],))
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
