"""腿 B 开跑前的口径检查：`busy_frac` 到底是不是**题面点名**要的，而不是我从真值反推的。

为什么还要这一条（P-05 只修了一半的话）：内核现在读题集里声明的 `busy_def`，
但那个声明是 `bench.py:_busy_definition` 拿"真值 `busy_frac` 与 `rho` 是否相等"**推**出来的。
只要推导结果没写进题面/契约，腿 B 就会造出假阳：一个每台利用率写对了的正确模型，
在 `mmcK` 上会挨 9–68% 的相对偏差——而这正是论文要抓的"口径错型"族。
所以这里验的是**载体**：每一道有忙度真值的题，契约里必须有一句定义原文（不是数字），
并单独报三档 `util / occupied / coincident` 的题数，供论文写"题面点名要哪个口径"这句。

判 FAIL 的条件：① 有真值忙度却没声明；② 声明了却没定义文字；③ 定义文字里两个名字都没出现。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('SC_BUSY_OUT') or os.path.join(HERE, 'BUSY_DEF_CONTRACT.md')
TASKSJ = os.environ.get('SC_TASKS_JSONL') or os.path.join(HERE, 'tasks.jsonl')
MUST_MENTION = (('E[min(N', '每台'), ('1−π₀', 'π0', '站不空'), ('恒等',))


def main():
    tasks = [json.loads(l) for l in io.open(TASKSJ, encoding='utf-8') if l.strip()]
    bad, by = [], {}
    for t in tasks:
        bf = (t.get('truth_raw') or {}).get('busy_frac')
        dfn = t.get('busy_def')
        ct = (t.get('contract') or {}).get('busy_frac') or \
             (t.get('output_contract') or {}).get('busy_frac')
        if bf is None:
            if dfn:
                bad.append('%s：没有忙度真值却声明了 busy_def=%s' % (t['task_id'], dfn))
            continue
        if not dfn:
            bad.append('%s：有忙度真值 %s 却没声明 busy_def（内核会 SystemExit，但那是跑起来才发现）'
                       % (t['task_id'], bf))
            continue
        by.setdefault(dfn, []).append(t['task_id'])
        if not ct:
            bad.append('%s：busy_def=%s 但契约里没有 busy_frac 的定义文字 ⇒ 腿 B 口径无载体'
                       % (t['task_id'], dfn))
            continue
        need = MUST_MENTION[{'util': 0, 'occupied': 1, 'coincident': 2}[dfn]]
        if not any(w in ct for w in need):
            bad.append('%s：busy_def=%s 的定义文字 %r 里没出现该口径的名字 %s ⇒ 等于没点名'
                       % (t['task_id'], dfn, ct[:60], need))
    lines = ['# 忙度口径有没有题面载体（`check_busy_def_text.py` 产生）', '',
             '- 题集 %d 题；**有忙度真值且已声明口径** %d 题；无忙度真值 %d 题' % (
                 len(tasks), sum(len(v) for v in by.values()),
                 sum(1 for t in tasks if (t.get('truth_raw') or {}).get('busy_frac') is None)), '',
             '| 声明 | 题数 | 题号 | 契约里的定义原文（示例） |', '|---|---|---|---|']
    sample = {}
    for t in tasks:
        if t.get('busy_def') and t['busy_def'] not in sample:
            sample[t['busy_def']] = (t.get('contract') or {}).get('busy_frac') or \
                (t.get('output_contract') or {}).get('busy_frac')
    for d in ('occupied', 'util', 'coincident'):
        if by.get(d):
            lines.append('| `%s` | %d | %s | %s |' % (
                d, len(by[d]), ' '.join(by[d]), (sample.get(d) or '(缺)')[:70]))
    lines += ['', '违规 %d 条%s' % (len(bad), '：' if bad else '（0 ⇒ 腿 B 的 `busy_frac` 判分有题面载体）'), '']
    for x in bad[:10]:
        lines.append('- %s' % x)
    lines += ['', '**还能不能算彻底**：`busy_def` 仍是由 `bench.py:_busy_definition` 拿真值与 `rho` '
              '的比较**推**出来的（相等 → `util`/`coincident`，不等 → `occupied`）。'
              '本文件证明的是"推出来的那个口径已经写进契约、题面可指认"，'
              '**不是**"推导独立于真值"。要后者，得让出题时用模型名（如"blocking probability" ↔ 1−π₀）'
              '而不是比数值——记在这里，别对他说这条已彻底闭合。', '']
    txt = '\n'.join(lines) + '\n'
    io.open(OUT, 'w', encoding='utf-8').write(txt)
    sys.stdout.buffer.write(txt.encode('utf-8'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
