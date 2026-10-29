"""把 8 个标定分片 `_recal_shard*.jsonl` 合并成 `RECAL64_raw.jsonl`，**条数不对就不合并**。

为什么要单独一个脚本：分片并行是为了快（4 小时压到 30 分钟），但并行的代价是
"少一片/半行/重复行"都可能被静默吃掉。这里把对账做成硬闸：
  - 每片必须存在且逐行可 `json.loads`（半行 = 直接停）；
  - 合并后必须正好 64 题 × {10 条 task 级 + 1 条 batch 级} = 704 行；
  - `(task_id, purpose, seed_start)` 不许重复，也不许出现 `error` 行混进统计；
  - 每行自带的 `seeds/horizon` 必须全等于当前口径（这一条与 `check_recal_currency.py` 的闸同源）。
"""
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHARDS = os.environ.get('RECAL_SHARDS') or os.path.join(HERE, '_recal_shard*.jsonl')
OUT = os.environ.get('RECAL_MERGED') or os.path.join(HERE, 'RECAL64_raw.jsonl')
WANT_SEEDS, WANT_HOR, NTRIAL = 10, 40000.0, 10


def main():
    files = sorted(glob.glob(SHARDS))
    if not files:
        raise SystemExit('没匹配到分片：%s（cwd=%s）' % (SHARDS, HERE))
    rows, errs, seen = [], [], {}
    batch_seeds = set()
    for fn in files:
        n = 0
        for ln, line in enumerate(io.open(fn, encoding='utf-8'), 1):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except ValueError:
                raise SystemExit('%s 第 %d 行不是完整 JSON ⇒ 分片被中断，重跑那一片再合并' % (fn, ln))
            k = (d['task_id'], d.get('purpose'), d.get('seed_start'))
            if k in seen:
                raise SystemExit('重复记录 %s（出现在 %s 与 %s）' % (k, seen[k], fn))
            seen[k] = fn
            if d.get('purpose') == 'task':
                if (d.get('seeds'), d.get('horizon')) != (WANT_SEEDS, WANT_HOR):
                    errs.append('task 行口径不符：%s %s seeds=%s hor=%s（应为 %s/%g）' % (
                        d['task_id'], d.get('purpose'), d.get('seeds'), d.get('horizon'),
                        WANT_SEEDS, WANT_HOR))
            else:
                # batch 行**本来就不是 10 种子**（R2 那一档是 100 种子切成的批），
                # 拿 task 的口径去要求它，会把每一次合法合并都判成"口径不符"——
                # 这个错是在 `neg_test_chain.py` 的 C3 正向对照里抓到的，不是真跑时才发现的。
                batch_seeds.add(int(d.get('seeds') or 0))
                if d.get('horizon') != WANT_HOR:
                    errs.append('batch 行 horizon=%s ≠ %g：%s' % (
                        d.get('horizon'), WANT_HOR, d['task_id']))
            if d.get('error'):
                errs.append('%s %s ss=%s 有 error：%s' % (
                    d['task_id'], d.get('purpose'), d.get('seed_start'), d['error'][-60:]))
            rows.append(d)
            n += 1
        print('[%s] %d 行' % (os.path.basename(fn), n), flush=True)
    if errs:
        raise SystemExit('口径/错误不合格 %d 条，前 8：%s' % (len(errs), errs[:8]))
    assert len(batch_seeds) == 1, 'batch 级 seeds 不唯一：%s ⇒ R2 那一档的口径没法确定' % sorted(batch_seeds)
    tasks = sorted({d['task_id'] for d in rows})
    n_task = sum(1 for d in rows if d.get('purpose') == 'task')
    n_batch = sum(1 for d in rows if d.get('purpose') == 'batch')
    assert n_task == len(tasks) * NTRIAL, 'task 级行数 %d ≠ 题数 %d × %d' % (n_task, len(tasks), NTRIAL)
    assert n_batch == len(tasks), 'batch 级行数 %d ≠ 题数 %d' % (n_batch, len(tasks))
    assert len(rows) == n_task + n_batch == len(seen), '总行数对不上账'
    if os.path.exists(OUT):
        raise SystemExit('%s 已存在 ⇒ 先把它改名归档（它是上一轮的证据，不许覆盖）' % OUT)
    with io.open(OUT, 'w', encoding='utf-8', newline='') as f:
        for d in rows:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')
    print('合并完成：%d 行 / %d 题（task %d + batch %d）→ %s' % (
        len(rows), len(tasks), n_task, n_batch, OUT))


if __name__ == '__main__':
    main()
