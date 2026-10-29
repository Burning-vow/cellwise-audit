"""受控 A/B：内核改动之后，参照件报出的**每一个数**必须与改动前逐位不变；
只许多出声明过的例外格（现在唯一一组是 mm1K 的 8 格 busy_frac）。

为什么必须有它（而不是"跑通了就行"）：这些改动都在**被验收过的内核**里。
计数器的正确性主张是"只观测不改计算"，而这句话本身可能就是错的——
比如我在 `pick_index` 里顺手改了选取顺序，或者契约声明选了另一个数组，
那么 L/W/busy 就会静默换值，主表整张作废还看不出来。
所以这里用腿 A 自己的判定出口（stage1）跑两遍做对照，比较 878 个格的 `gate` 与 `est`。
任何 gate 翻转或不在例外清单里的 est 变化都要指名道姓，不许 summarize。

⚠ 三处 2026-10-17 的更正（外部审计 F-5）：
1. **这次对照是双因子的**（触发计数器 + `busy_frac` 口径改读契约），标题与判决都照实写；
   那 8 格例外只能归因到"口径改读契约"这一支（`trig_*` 不参与任何判据），
   计数器那一支要**单因子**再跑一次：在 temp 副本里把计数器行剥掉、`busy_def` 保持不动，
   那一版要求 **0 格例外**（连 mm1K 都不许变）。
2. 基线**不能**是 `P0_CROSSCHECK.csv`：那次新跑的 `P0_OUT` 没设对，交付件被新臂覆盖了，
   于是"基线 = 改动前那次"这句话指着一个装着改动后读数的文件。真基线在
   `_archive_superseded/P0_CROSSCHECK_pre_trig_2026-10-17.csv`（13:26，mm1K-01 est=0.565649）。
   现在加硬闸：`BASE == NEW` 直接 `SystemExit`。
3. 例外明细表原来印的是 `stage·pert`（`J1·none`），观测量名丢了 ⇒ 改成 `stage·obs`。
"""
import csv
import hashlib
import io
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
# 基线 = 改动前那次 stage1 的**归档件**（默认值就是它，别再指着会被覆盖的交付件）
BASE = os.environ.get('AB_BASE') or os.path.join(
    HERE, '_archive_superseded', 'P0_CROSSCHECK_pre_trig_2026-10-17.csv')
NEWF = os.environ.get('AB_NEW') or os.path.join(HERE, 'P0_CROSSCHECK.csv')
OUT = os.environ.get('AB_OUT') or os.path.join(HERE, 'AB_REF_NO_SIDE_EFFECTS.md')
# 这一版对照里到底改了哪几处——写进报告，不许让读者猜（规矩 18 的同族：句子要有载体）
FACTORS = os.environ.get('AB_FACTORS') or '触发计数器 + busy_frac 口径改读契约（**双因子**，见 §20-D）'

# 允许变的格子（**必须是修 bug 的必然后果**，且要写清为什么必须变）。
# mm1K 的 8 题 J1|busy_frac：真值给的是 1−π₀（mm1K-01：busy_frac=0.566273、rho=0.6 是到达负荷，差 0.0337），
# 而旧内核只对 mmcK 特判 occupancy，于是 mm1K 被拿去报"每台利用率"。
# P-05 把口径改成"读契约声明"之后，mm1K 按声明取 occupancy ⇒ 这两个数组在 c=1 上差第 6 位小数。
# 判定不许变：|Δrel| 必须在容差内，且 gate 一律不变（gate 变了就是硬失败）。
ALLOWED = {('mm1K', 'J1', 'busy_frac'): 1e-4}


def allowed_key(row):
    return (row.get('template'), row.get('stage'), row.get('obs'))


def load(path):
    m = {}
    for r in csv.DictReader(io.open(path, encoding='utf-8')):
        k = (r['task_id'], r['stage'], r.get('pert', ''), r.get('obs', ''))
        if k in m:
            raise SystemExit('基线表里有重复键 %s ⇒ 先查是谁写了两次' % (k,))
        m[k] = r
    return m


def manifest(path):
    if not os.path.exists(path):
        return '%s：**不在盘上**' % os.path.basename(path)
    h = hashlib.md5(io.open(path, 'rb').read()).hexdigest()[:12]
    n = sum(1 for _ in csv.DictReader(io.open(path, encoding='utf-8')))   # 行数≠记录数
    return ('%s：%d 行，mtime %s，md5 %s' % (
        os.path.relpath(path, HERE), n,
        time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(path))), h))


def main():
    if os.path.abspath(BASE) == os.path.abspath(NEWF):
        raise SystemExit('基线和新臂是同一个文件 %s ⇒ 这等于自己跟自己比。'
                         '要么把基线指到归档件，要么把新跑写到别的文件（P0_OUT）' % BASE)
    compare_only = '--compare-only' in sys.argv      # 跑一次 stage1 要 ~40 分钟，比对可单独重做
    if compare_only:
        for p in (BASE, NEWF):
            if not os.path.exists(p):
                raise SystemExit('--compare-only 但 %s 不存在' % p)
    else:
        if os.path.abspath(NEWF) == os.path.abspath(os.path.join(HERE, 'P0_CROSSCHECK.csv')):
            print('[注意] 新臂就是交付件 P0_CROSSCHECK.csv，基线用的是归档件 ⇒ 交付件会被更新，'
                  '但对照仍然成立（基线另在别处）', flush=True)
        if os.path.exists(NEWF):
            os.remove(NEWF)                    # stage1 是追加写的，残留半截会让键对不上账
        env = dict(os.environ)
        env['P0_OUT'] = NEWF
        env['PYTHONIOENCODING'] = 'utf-8'
        p = subprocess.run([PY, '-u', os.path.join(HERE, 'run_p0_crosscheck.py')],
                           cwd=HERE, env=env, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=7200)
        if p.returncode != 0:
            raise SystemExit('stage1 新跑失败 rc=%s：%s' % (
                p.returncode, (p.stdout or '')[-400:] + (p.stderr or '')[-400:]))
    old, new = load(BASE), load(NEWF)
    only_old, only_new = sorted(set(old) - set(new)), sorted(set(new) - set(old))
    flips, est_diff, allowed_hit = [], [], []
    for k in sorted(set(old) & set(new)):
        a, b = old[k], new[k]
        if a['gate'] != b['gate']:
            flips.append((k, a['gate'], b['gate']))     # 判定翻一点就硬失败，不给例外
        if (a.get('est') or '') != (b.get('est') or ''):
            ak = allowed_key(b)
            if ak in ALLOWED:
                try:
                    d = abs(float(b['rel']) - float(a['rel']))
                except (TypeError, ValueError):
                    d = float('inf')
                if d <= ALLOWED[ak]:
                    allowed_hit.append((k, a.get('est'), b.get('est'), a.get('rel'), b.get('rel'), d))
                    continue
            est_diff.append((k, a.get('est'), b.get('est')))
    lines = ['# 受控 A/B：内核改动（%s）⇒ 参照件读数逐位不变？' % FACTORS, '',
             '对照的两个臂（**报告里的文件名必须能在盘上找到**，审计 F-5）：',
             '- 基线 = %s' % manifest(BASE),
             '- 新臂 = %s%s' % (manifest(NEWF),
                                '（本次只比对，未重跑）' if compare_only else '（本次重跑产生）'),
             '- 本次调用 argv = `%s`' % ' '.join(sys.argv[1:] or ['(无)']), '',
             '- 共同格 %d；只在基线里 %d；只在新表里 %d' % (
                 len(set(old) & set(new)), len(only_old), len(only_new)),
             '- **gate 翻转：%d 格**（要求 0，无例外）%s' % (
                 len(flips), '' if not flips else '，前 5：%s' % flips[:5]),
             '- **意外 est 变化：%d 格**（要求 0）%s' % (
                 len(est_diff), '' if not est_diff else '，前 5：%s' % est_diff[:5]),
             '- **声明过的例外变化：%d 格**（只允许 %s，且 |Δrel| ≤ %g）' % (
                 len(allowed_hit), ', '.join('%s/%s' % (t, o) for (t, _, o) in ALLOWED),
                 min(ALLOWED.values())), '']
    if allowed_hit:
        lines += ['## 声明例外的逐格明细（修 bug 的必然后果，判定不变）', '',
                  '| 题号 | 判据/观测量 | 旧 est | 新 est | 旧 rel | 新 rel | 绝对差 rel |',
                  '|---|---|---|---|---|---|---|']
        for k, oe, ne, orl, nrl, d in allowed_hit:
            lines.append('| %s | %s·%s | %s | %s | %s | %s | %.2e |' % (
                k[0], k[1], k[3], oe, ne, orl, nrl, d))
        lines += ['', '这 8 格为什么**必须**变（不是副作用，是修口径的必然后果）：`mm1K` 的真值 `busy_frac`'
                  ' 是 `1−π₀`（mm1K-01 = 0.566273，而 `rho = 0.6` 是到达负荷），旧内核只对 `mmcK` 特判'
                  ' occupancy，于是 `mm1K` 被拿去报"每台利用率"的**估计子**。两式在 `c=1` 上理论恒等，'
                  '有限窗口的边界处理不同 ⇒ 差第 6 位小数。**所以这一支归因到"口径改读契约"，'
                  '与计数器无关。**', '']
    ok = (not flips and not est_diff and not only_old and not only_new
          and len(allowed_hit) <= len(ALLOWED) * 8)
    lines += ['## 判决', '',
              ('PASS ⇒ 除上面**声明过的例外格**之外，参照件读数逐位不变、gate 零翻转：本次对照覆盖的'
               '改动（%s）没有落到读数上的副作用。' % FACTORS if ok else
               'FAIL ⇒ 出现了不在允许清单里的读数变化或 gate 翻转：先把"该不该变"解释清楚，'
               '再决定要不要重跑标定表与主矩阵。'), '',
              '⚠ 这句话的**边界**：这是双因子对照，不能把"没有副作用"归因到单个改动上。'
              '计数器那一支的单因子复验（temp 副本里剥掉计数器、`busy_def` 不动，要求 0 格例外）'
              '记在 `预注册 §20-D` 的待办里。', '',
              '例外清单是代码里的 `ALLOWED`（带容差与理由），不是临时改判据：'
              '往清单里加一条 = 承认一处副作用，必须同时在预注册里记一笔。', '']
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
