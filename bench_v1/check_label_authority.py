"""标签双权威对账（2026-10-18，`selfcheck_all` 第 15 项）。

要挡的东西：`mutants.jsonl` 里的 `expected` 是**生成产物**，它的源头是 `simcore.CATALOG`。
10-17 给 E35 改判时只写了产物没写成源头（改判脚本的正则静默没匹配上，只 print 不 assert），
于是盘上出现"产物说 detectable、源头说 benign"。这不改变当天任何一张表的读数
（`summarize_matrix_v2.py` 只读 `mutants.jsonl`），但它是颗雷：
任何人重跑 `make_mutants.py gen` 都会把 E35 盖回 benign ⇒ 良性分母从 68 变 74、
可检分母从 186 变 180，而且**不会报错**。

所以这里做的不是"再存一份标签"，而是**要求两份权威必须逐格相等**：
  对 `mutants.jsonl` 的每一行 (task_id, error_type)：`expected_for(error_type, template)`
  （CATALOG 侧，含 `expected_by_tpl` 逐模板覆盖）必须等于产物里写的那一个。
反方向也查：CATALOG 声明 `applies` 到某模板、产物里却没有对应行 ⇒ 说明产物是旧的。
"""
import io
import json
import os
import sys
import collections
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import simcore as SC            # noqa: E402
from make_mutants import expected_for   # noqa: E402  ← 单一实现，不在这里重写查表

MUT = os.environ.get('LA_MUTANTS') or os.path.join(HERE, 'mutants.jsonl')
OUT = os.environ.get('LA_OUT') or os.path.join(HERE, 'LABEL_AUTHORITY.md')
TASKS = {t['task_id']: t for t in SC.load_tasks()}


def emit(s):
    try:
        sys.stdout.write(s + '\n')
    except UnicodeEncodeError:
        sys.stdout.buffer.write(s.encode('utf-8', 'replace').decode('utf-8').encode(
            'utf-8', 'replace') + b'\n')


def main():
    rows = [json.loads(l) for l in io.open(MUT, encoding='utf-8') if l.strip()]
    assert rows, 'mutants.jsonl 是空的'
    bad = []
    for r in rows:
        src = expected_for(r['error_type'], r['template'])
        if src != r['expected']:
            bad.append((r['task_id'], r['error_type'], r['template'], r['expected'], src))
    # 反方向：CATALOG 说这个错型适用这个模板，产物里却没有这一格
    have = {(r['error_type'], r['template']) for r in rows}
    missing = []
    for et, c in sorted(SC.CATALOG.items()):
        for tpl in c['applies']:
            if (et, tpl) not in have and tpl in {t['template'] for t in TASKS.values()}:
                missing.append((et, tpl))
    per_label = collections.Counter(r['expected'] for r in rows)
    n_items = len({(r['task_id'], r['error_type']) for r in rows})
    lines = ['# 标签双权威对账（`check_label_authority.py` 产生）', '',
             '生成时间：%s ｜ 产物行 %d ｜ 工件 %d 件' % (
                 datetime.now().strftime('%Y-%m-%d %H:%M:%S'), len(rows), n_items), '',
             '- 每行标签 = 产物 `mutants.jsonl` 的 `expected` vs 源头 `simcore.CATALOG`'
             '（经 `make_mutants.expected_for`，含 `expected_by_tpl` 逐模板覆盖）',
             '- **不一致 %d 行**；源头声明适用但产物缺格 %d 项' % (len(bad), len(missing)),
             '- 标签分布（现算，别处不许抄这个数）：%s' % (
                 '、'.join('%s %d' % (k, v) for k, v in sorted(per_label.items()))), '']
    if bad:
        lines.append('## 不一致明细（**必须清零**）')
        lines.append('| task | 错型 | 模板 | 产物说 | 源头说 |')
        lines.append('|---|---|---|---|---|')
        for b in bad:
            lines.append('| %s | %s | %s | %s | %s |' % b)
    if missing:
        lines.append('## 源头声明适用、产物里没有的 (错型,模板)')
        for m in missing:
            lines.append('- %s / %s' % m)
    lines.append('')
    lines.append('读法：`summarize_matrix_v2.py` 只认 `mutants.jsonl`，所以今天所有表的标签是对的；'
                 '这道闸保的是"重跑生成器不会把改判盖回去"。两条权威任何一条动了都必须在这里露出来。')
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    emit('[label_authority] 行=%d 工件=%d 不一致=%d 源头多声明=%d 标签=%s' % (
        len(rows), n_items, len(bad), len(missing),
        ','.join('%s:%d' % (k, v) for k, v in sorted(per_label.items()))))
    if bad or missing:
        emit('FAIL：标签两份权威不同源（详见 LABEL_AUTHORITY.md）')
        return 1
    emit('PASS：CATALOG 与 mutants.jsonl 逐格一致，且无"源头有、产物无"的缺格')
    return 0


if __name__ == '__main__':
    sys.exit(main())
