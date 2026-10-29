"""表 4 的替代版：**工作量表**，不需要任何人类计时。

为什么要换轴：原方案是仿《系统仿真学报》B 篇表 4（自动生成 h vs 手工生成 h）。
那一列要一个"人工核对耗时"的实测数，做这个动作的人是他，他明确说做不了。
**没有人类被试就不许编一个 h 上去**，所以这张表只报同一单位下的**工作量**与
仪器**自身实测墙钟**，不报"快 N 倍"。

两处必须先钉住的口径（都是本轮自己踩出来的）：
1. **腿 A 的注入工件是 17 行的调用壳**（与 `*_REF.py` 的唯一代码差是最后一行错型代号），
   真逻辑在 `simcore.py` 内核。所以**腿 A 不许用"代码行"当人工工作量**——那是我的壳，
   不是被审对象。腿 A 只用"判据判决条数"这个真单位。
2. **仪器墙钟必须把超时件算进去**：腿 B 那 8 件 420 s 未跑完的，单件成本是正常件的 1400 倍，
   只统计 OK 件会把仪器成本严重低估。
"""
import csv
import io
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MUTANTS = os.path.join(HERE, 'mutants.jsonl')
TAGS = os.path.join(HERE, 'MUTANT_TAGS_R10c.csv')
LEGB = os.path.join(HERE, '_rejudge_flash20261018_v2.txt')
OUT = io.open(os.path.join(HERE, 'TABLE4_WORKLOAD.md'), 'w', encoding='utf-8')

# 超时件的判据：run_note 里印着我给的预算秒数
TIMEOUT_MARK = 'timed out'


def w(s=''):
    OUT.write(s + '\n')


def fmt(x):
    return '{:,}'.format(x)


def load_jsonl(path):
    return [json.loads(l) for l in io.open(path, encoding='utf-8') if l.strip()]


def main():
    problems = []
    muts = load_jsonl(MUTANTS)
    with io.open(TAGS, encoding='utf-8') as f:
        tags = list(csv.DictReader(f))
    if len(muts) != len(tags):
        problems.append('mutants=%d 与 tags=%d 条数不等 ⇒ 分母不可用' % (len(muts), len(tags)))
    tk = {(r['task_id'], r['error_type']): r for r in tags}
    if len(tk) != len(tags):
        problems.append('tags 有重复键：唯一 %d / 行 %d' % (len(tk), len(tags)))

    # ---- 腿 A：先自证"壳"这个前提，前提不成立就不许用下面的写法 ----
    shell_sizes = Counter()
    for m in muts:
        p = os.path.normpath(os.path.join(ROOT, m['artifact_path'].replace('\\', '/')))
        if not os.path.exists(p):
            problems.append('缺文件 %s' % m['artifact_path'])
            continue
        with io.open(p, encoding='utf-8', errors='replace') as f:
            shell_sizes[sum(1 for _ in f)] += 1
    n_shells = sum(shell_sizes.values())
    is_uniform_shell = len(shell_sizes) == 1
    w('# 表 4\u2032 工作量表（无人类计时；`TABLE4_WORKLOAD.py` 现算）\n')
    w('## 0. 先声明这张表能用什么单位\n')
    w('- 腿 A 注入工件 **%d 件**，实测文件行数只有 %d 种取值（%s）⇒ '
      '**确认是调用壳**（真逻辑在 `simcore.py`）。' % (
          n_shells, len(shell_sizes),
          '、'.join('%d 行×%d 件' % (k, v) for k, v in sorted(shell_sizes.items()))))
    w('- ⇒ **腿 A 一侧禁用"代码行"当人工工作量**（那是壳的行数，不是被审对象的大小）。'
      '腿 A 只报**判据判决条数**。\n')
    if not is_uniform_shell and n_shells:
        problems.append('腿 A 工件行数不再是单一取值（%s 种）⇒ 上面"壳"的断言要重核'
                        % len(shell_sizes))

    rows = []
    for m in muts:
        t = tk.get((m['task_id'], m['error_type']))
        if t is None:
            problems.append('tags 里找不到 %s__%s' % (m['task_id'], m['error_type']))
            continue
        rows.append({'key': '%s__%s' % (m['task_id'], m['error_type']),
                     'fired': int(t['fired_A'] or 0), 'tag': t['tag_strict_A'],
                     'nrows': int(t['rows'] or 0), 'ran': int(t['ran'] or 0)})
    verdict_rows = sum(r['nrows'] for r in rows)
    w('## 1. 腿 A：仪器产出了多少条判决，人真正需要复核的是哪一档\n')
    w('| 分组 | 件数 | 判据判决条数 | 占件 | 占判决条数 |')
    w('|---|---|---|---|---|')
    fired = [r for r in rows if r['fired'] >= 1]
    quiet = [r for r in rows if r['fired'] == 0 and r['ran'] == 1]
    for name, sel in [('全部件', rows), ('至少一格点火（=人该复核的）', fired),
                      ('全程不点火', quiet)]:
        nr = sum(r['nrows'] for r in sel)
        w('| %s | %d | %s | %s | %s |' % (
            name, len(sel), fmt(nr),
            '%.1f%%' % (100.0 * len(sel) / len(rows)) if rows else '—',
            '%.1f%%' % (100.0 * nr / verdict_rows) if verdict_rows else '—'))
    w('')
    w('### 按判定身份拆\n')
    w('| 标签 | 件数 | 判决条数 | 这一档人读了有没有用 |')
    w('|---|---|---|---|')
    NOTE = {'TP': '有用——复核仪器判对的那格',
            'BLIND_CONFIRM': '**没用**——定理说这类逐位恒等，人读也读不出（仪器已认）',
            'BENIGN_OK': '抽样即可——本来就该绿',
            'WEAK_FIRED': '有用——幅度不足的那档',
            'INJECTION_IDLE': '不用——注入空转，判定身份已剔除'}
    for tag in sorted({r['tag'] for r in rows}):
        sel = [r for r in rows if r['tag'] == tag]
        w('| %s | %d | %s | %s |' % (tag, len(sel), fmt(sum(r['nrows'] for r in sel)),
                                    NOTE.get(tag, '—')))
    w('')

    # ---- 腿 B：真代码，行数单位在这里才合法 ----
    if os.path.exists(LEGB):
        recs = [json.loads(s) for s in io.open(LEGB, encoding='utf-8')
                if s.strip().startswith('{')]
        lines_of = lambda rs: sum(int(r.get('code_lines') or 0) for r in rs)
        ok = [r for r in recs if r.get('kind') == 'OK']
        alarms_items = [r for r in recs
                        if int(r.get('n_tot') or 0) > int(r.get('n_in') or 0)]
        cells_tot = sum(int(r.get('n_tot') or 0) for r in recs)
        cells_in = sum(int(r.get('n_in') or 0) for r in recs)
        timed = [r for r in recs if TIMEOUT_MARK in str(r.get('run_note') or '').lower()]
        wall_all = [float(r['run_wall']) for r in recs if r.get('run_wall') is not None]
        wall_ok = [float(r['run_wall']) for r in ok if r.get('run_wall') is not None]
        wall_to = [float(r['run_wall']) for r in timed if r.get('run_wall') is not None]

        w('## 2. 腿 B（flash 臂真实工件）：**这里"代码行"才是被审对象的真实大小**\n')
        w('| 分组 | 件数 | 代码行 | 占件 | 占代码行 |')
        w('|---|---|---|---|---|')
        tl = lines_of(recs)
        for name, sel in [('全部件（=逐件逐行核对的下界）', recs),
                          ('至少报警一格（=人该复核的）', alarms_items),
                          ('能出判定行（OK）', ok)]:
            cl = lines_of(sel)
            w('| %s | %d | %s | %s | %s |' % (
                name, len(sel), fmt(cl),
                '%.1f%%' % (100.0 * len(sel) / len(recs)) if recs else '—',
                '%.1f%%' % (100.0 * cl / tl) if tl else '—'))
        w('')
        w('- 证据格 **%d**，其中与闭式真值不一致（报警）**%d（%s）**；'
          '件级：报警件 **%d/%d（%s）**。\n' % (
              cells_tot, cells_tot - cells_in,
              '%.1f%%' % (100.0 * (cells_tot - cells_in) / cells_tot) if cells_tot else '—',
              len(alarms_items), len(recs),
              '%.1f%%' % (100.0 * len(alarms_items) / len(recs)) if recs else '—'))

        w('## 3. 仪器自身成本（实测墙钟，无人参与；**含超时件**）\n')
        w('| 口径 | 件数 | 合计 s | 中位 s | 最长 s |')
        w('|---|---|---|---|---|')
        for name, ws in [('全部有墙钟记录的件', wall_all), ('只算 OK 件（会低估）', wall_ok),
                         ('只算 420 s 超时件', wall_to)]:
            if not ws:
                w('| %s | 0 | — | — | — |' % name)
                continue
            srt = sorted(ws)
            w('| %s | %d | %s | %.2f | %.1f |' % (
                name, len(srt), fmt(round(sum(ws), 1)), srt[len(srt) // 2], max(ws)))
        w('')
        if wall_ok and wall_to:
            w('> **只统计 OK 件会把仪器成本少算 %.1f 倍**（%s s vs %s s）；'
              '超时 %d 件是"工件在 R=10/40000 下算不动"，属被审对象的成本，不属仪器判分的成本，'
              '所以正文要分两栏报，不许合并成一个平均数。\n' % (
                  sum(wall_all) / max(sum(wall_ok), 1e-9),
                  fmt(round(sum(wall_all), 1)), fmt(round(sum(wall_ok), 1)), len(timed)))
    else:
        problems.append('腿 B 文件缺失：%s' % LEGB)

    w('## 4. 允许说 / 禁写\n')
    w('- ✅ 允许：腿 A 上仪器产出 %s 条判决，其中落在"至少点火一次"的 %d 件上；'
      '定理判定的恒等类 %d 件（%s 条判决）明确写了"人读也读不出"。' % (
          fmt(verdict_rows), len(fired),
          len([r for r in rows if r['tag'] == 'BLIND_CONFIRM']),
          fmt(sum(r['nrows'] for r in rows if r['tag'] == 'BLIND_CONFIRM'))))
    if os.path.exists(LEGB):
        w('- ✅ 允许：腿 B 上逐件逐行核对要读 %s 行，只看报警件是 %s 行（**行数比，不是时间比**）。' % (
            fmt(tl), fmt(lines_of(alarms_items))))
    w('- ❌ 禁写："比人工快 N 倍""节省 X 小时"——人工侧没有秒数、没有人类被试。\n')
    w('- ❌ 禁写：用腿 A 的壳行数当工作量（§0 已自证是壳）。\n')
    w('- ⚠ 若将来真做人工侧：需要独立读者 + 计时协议 + 预注册中止条件；'
      '读者不能是我（错型目录与判据是我写的，读自己是循环），也不能是他（已说明做不了）。\n')

    w('## 5. 对账与退出码\n')
    if problems:
        for p in problems:
            w('- **%s**' % p)
    else:
        w('- 无：mutants=%d、tags=%d、取到判决=%d、判决条数=%s，分母互相对上。' % (
            len(muts), len(tags), len(rows), fmt(verdict_rows)))
    OUT.close()
    if problems:
        sys.exit(1)
    print('OK legA=%d legB=%d' % (len(rows), len(recs) if os.path.exists(LEGB) else 0))


if __name__ == '__main__':
    main()
