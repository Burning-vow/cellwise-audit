"""主表层面的"改动有没有落到读数上"对照：`MUTANT_MATRIX_R10`（改前）vs `R10b`（改后）。

为什么 stage1 那次 A/B 不够（外部审计 F-5 + "它说重的第几条"最后一条）：
`AB_REF_NO_SIDE_EFFECTS.md` 只验了 64 个**参照件**，而主表是 346 件 × 变异体，
计数器的代码路径（`pick_index` / 预占 / 网络转移）**只有在变异体上才被绕开或高频触发**；
更要紧的是：如果计数器改动动了随机数流或选取顺序，受害的是变异体那一侧的 rel，不是参照件。

⚠ 这张对照是**三因子**的（改前那份分片是 13:49–14:08 产的，其间还改过
`criteria.py`(15:58) 的出口字段清单），所以它只能给出"合并起来没有副作用"这一条上界证据，
**不能把功劳归到单个改动**。归因到计数器单一支，靠的是 `check_trig_no_side_effects.py`
在 temp 副本里剥掉计数器再跑一次 stage1（`预注册 §20-D`）。

判据：
  1) 两份矩阵的键集必须完全相同（缺件/多件 = 分片没跑齐，直接停）；
  2) `rel` 逐字符相同，除非该格落在**声明过的例外清单**里（`mm1K` 的 `busy_frac` 相关格）；
  3) `fired_*` 四列必须与 `rel` 同生同灭：例外清单外的格若 `rel` 相同而 `fired` 不同，
     说明判据本身变了（那是 `criteria` 那一支，不是计数器），必须单列报出来。
"""
import collections
import csv
import glob
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OLD = sys.argv[1] if len(sys.argv) > 1 else 'MUTANT_MATRIX_R10.shard*.csv'
NEW = sys.argv[2] if len(sys.argv) > 2 else 'MUTANT_MATRIX_R10b.shard*.csv'
OUT = os.environ.get('MX_OUT') or os.path.join(HERE, 'AB_MATRIX_NO_SIDE_EFFECTS.md')
# 例外：口径改读契约之后，只有"吃 busy_frac 的格"允许换读数。
ALLOWED_TPL_OBS = {('mm1K', 'busy_frac')}
FIRED = ('fired_0.01', 'fired_0.02', 'fired_0.03', 'fired_0.05')


def load(pat):
    files = sorted(f for f in glob.glob(os.path.join(HERE, pat))
                   # `MUTANT_MATRIX_R10b.shard*.csv` 这个 glob **也会**匹配到伴生的
                   # `.triggers.csv`（表头没有 stage 列）⇒ 必须显式排掉，不然读进去就是 KeyError。
                   if '.triggers.' not in os.path.basename(f))
    if not files:
        raise SystemExit('glob 没匹配到任何文件：%s（cwd=%s）⇒ 别拿空结果当"没有差异"' % (pat, HERE))
    m, rows = {}, 0
    for fn in files:
        for r in csv.DictReader(io.open(fn, encoding='utf-8')):
            k = (r['key'], r['task_id'], r['error_type'], r['stage'],
                 r.get('instance') or r.get('obs') or '')
            if k in m:
                raise SystemExit('%s 里重复键 %s ⇒ 先查是谁写了两次' % (os.path.basename(fn), k))
            m[k] = r
            rows += 1
    return m, rows, [os.path.basename(f) for f in files]


def obs_of(r):
    """矩阵的观测量名就在 `instance` 列（J1 行 = W/L/busy_frac/…，J2/J3 行 = J2a_little/…）。"""
    return (r.get('instance') or '').strip()


def main():
    old, n_old, f_old = load(OLD)
    new, n_new, f_new = load(NEW)
    only_old, only_new = sorted(set(old) - set(new)), sorted(set(new) - set(old))
    same_rel, diff_rel, allowed_diff, fired_diff = 0, [], [], []
    kinds = collections.Counter()
    for k in sorted(set(old) & set(new)):
        a, b = old[k], new[k]
        # 空 rel（判不了）两边必须都空，否则"判不了"的身份变了
        if (a.get('rel') or '') != (b.get('rel') or ''):
            tpl = a.get('template')
            o = obs_of(a) or obs_of(b)
            if (tpl, o) in ALLOWED_TPL_OBS and (a.get('rel') or '') and (b.get('rel') or ''):
                allowed_diff.append((k, a.get('rel'), b.get('rel')))
            else:
                diff_rel.append((k, a.get('rel'), b.get('rel'), tpl, o))
                kinds['rel 不同（例外清单外） tpl=%s obs=%s' % (tpl, o)] += 1
            continue
        same_rel += 1
        fr = [(x, a.get(x), b.get(x)) for x in FIRED if (a.get(x) or '') != (b.get(x) or '')]
        if fr:
            fired_diff.append((k, fr))
            kinds['rel 相同但 fired_* 变了（判据变，不是内核变）'] += 1
    lines = ['# 主表层面：改前 / 改后矩阵的逐格对照（**三因子合并，不能单归因**）', '',
             '- 旧 = `%s` → %s（%d 行）' % (OLD, ','.join(f_old), n_old),
             '- 新 = `%s` → %s（%d 行）' % (NEW, ','.join(f_new), n_new),
             '- 共同键 %d；只在旧 %d；只在新 %d' % (len(set(old) & set(new)), len(only_old), len(only_new)),
             '- `rel` 逐字符相同：%d 格' % same_rel,
             '- **例外清单外的 rel 变化：%d 格**（要求 0）' % len(diff_rel),
             '- 例外清单内（%s）的 rel 变化：%d 格' % (
                 ','.join('%s/%s' % t for t in sorted(ALLOWED_TPL_OBS)), len(allowed_diff)),
             '- **rel 相同但 `fired_*` 变了：%d 格**（要求 0；不为 0 = `criteria` 那一支在动判定，'
             '与计数器无关，必须单列）' % len(fired_diff), '']
    if kinds:
        lines += ['## 变化按类型计数', '']
        for kk, v in kinds.most_common():
            lines.append('- %s：%d 格' % (kk, v))
        lines.append('')
    if diff_rel:
        lines += ['## 例外清单外的逐格明细（前 40）', '',
                  '| key | task | 错型 | stage | instance | 旧 rel | 新 rel | 模板 | 观测量 |',
                  '|---|---|---|---|---|---|---|---|---|']
        for k, ra, rb, tpl, o in diff_rel[:40]:
            lines.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
                k[0], k[1], k[2], k[3], k[4], ra, rb, tpl, o or '(取不到)'))
        lines.append('')
    if allowed_diff:
        lines += ['## 例外清单内的读数变化（前 20，用于核"确实只是 busy_frac 换估计子"）', '']
        for k, ra, rb in allowed_diff[:20]:
            lines.append('- %s %s/%s %s：`rel` %s → %s' % (k[1], k[2], k[3], k[4], ra, rb))
        lines.append('')
    if fired_diff:
        lines += ['## `fired_*` 与 `rel` 不同步的格（前 20）', '']
        for k, fr in fired_diff[:20]:
            lines.append('- %s %s/%s：%s' % (k[1], k[2], k[3], fr))
        lines.append('')
    ok = not only_old and not only_new and not diff_rel and not fired_diff
    lines += ['## 判决', '',
              ('PASS ⇒ 本次比对的 %d 格里，除了声明过的 %d 格 `mm1K/busy_frac`，改前改后的 `rel` '
               '与 `fired_*` 逐字符相同。这句话**只**说明"这几处改动合起来没落到读数上"。'
               % (same_rel + len(allowed_diff), len(allowed_diff)) if ok else
               'FAIL ⇒ 有例外清单外的读数变化或 `fired_*` 与 `rel` 不同步：先归因（内核 or 判据），'
               '再决定主表要不要重跑；**不许**先把比率写进论文。'), '',
              '旧分片（13:49–14:08）与新分片（21:0x）之间一共动过三处：'
              '`criteria.py` 15:58 的出口字段清单、`simcore.py` 20:02 的触发计数器与 `busy_def`、'
              '`tasks.jsonl` 20:03 新增 `busy_def` 字段。单因子归因见 `AB_REF_NO_SIDE_EFFECTS.md` 与 §20-D。', '']
    txt = '\n'.join(lines) + '\n'
    io.open(OUT, 'w', encoding='utf-8').write(txt)
    sys.stdout.buffer.write(txt.encode('utf-8'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
