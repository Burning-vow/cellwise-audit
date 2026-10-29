"""今晚这条链的顺序驱动器：一步不过就停下，不许"先跑完再说"。

顺序是 `预注册 §20-C` 钉死的，写进代码是为了让"顺序"这件事不依赖我记得：
  0) sync_artifact_docstrings  工件头注释与 CATALOG 对齐（只改注释行，自己证明读数没变）【10-18 加】
  1) merge_recal_shards     8 片 → RECAL64_raw.jsonl（必须正好 64 题 × 11 = 704 条）
  2) build_tables_v2        → table_tau_v2.csv / table_FP_v2.csv（旧表已在归档里留了副本）
  3) diff_tau_tables        旧表 vs 新表：τ* 有没有换档 ⇒ **决定主矩阵要不要重跑**
  4) fix_e35_label          P-04：E35 改判写回标签源头（**这一步会改 simcore.py**）
  5) check_benign           重建 BENIGN_PROOF（R=10，逐件自证）
  6) run_p0_crosscheck      stage1 整批重跑（先归档旧 CSV，因为它追加写）【10-18 加，J0 要出行】
  7) check_recal_currency   要求 0 DRIFT，且必须排在 4 之后（第 3 项自检是按 mtime 判新鲜度的）
  8) summarize_matrix_v2    正式主表汇总（R10b 四片 + 触发表）
  9) neg_test_selfcheck + selfcheck_all   先验闸会红，再看闸红不红
 10) build_field_contract + check_contract_gates   契约重建 + 两条闸复验

每一步都打"前置产物的条数/口径"，不对就停：今天两次事故都是"半截产物被当成完整产物往下游用"。
"""
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
LOG = os.environ.get('CHAIN_LOG') or os.path.join(HERE, '_chain_20261017.log')
# 换档对账的"旧表"：10-18 这轮要比的是 J0 上线前那张表（已随分片一起归档）。
# 做成环境变量是因为驱动器每一步的输入都必须能指认，不然 diff 出来的"一致"是哪两张表一致？
OLD_TAU = os.environ.get('CHAIN_OLD_TAU') or os.path.join(
    HERE, '_archive_superseded', 'recal_preJ0_2026-10-17', 'table_tau_v2.csv')
N_TASK_ALL = 64


def sh(cmd, env=None, timeout=7200):
    e = dict(os.environ, PYTHONIOENCODING='utf-8')
    e.update(env or {})
    print('\n$ %s' % ' '.join(cmd), flush=True)
    p = subprocess.run(cmd, cwd=HERE, env=e, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    out = ((p.stdout or '') + (p.stderr or ''))
    tail = [l for l in out.strip().splitlines() if l.strip()][-4:]
    for l in tail:
        print('   | ' + l[:170], flush=True)
    return p.returncode, out, tail


def step(no, name, cmd, env=None, want_rc=0, timeout=7200):
    rc, out, tail = sh(cmd, env, timeout)
    ok = (rc == want_rc)
    print('[步骤 %s] %s —— %s (rc=%s)' % (no, name, '过' if ok else '**停**', rc), flush=True)
    if not ok:
        print(out[-1500:], flush=True)
        raise SystemExit('步骤 %s（%s）没过 ⇒ 链停下。不要往下游搬数字。' % (no, name))
    return out


def count_jsonl(p):
    return sum(1 for l in io.open(p, encoding='utf-8') if l.strip())


def main():
    only = sys.argv[1:]                     # 可只跑某几步：`python run_chain_20261017.py 3 4`
    t0 = time.time()
    log = io.open(LOG, 'a', encoding='utf-8')
    log.write('\n==== 链开始 %s argv=%s ====\n' % (time.strftime('%m-%d %H:%M'), only or '全部'))

    def todo(n):
        return (not only) or (str(n) in only)

    # ⚠ 顺序里有一个坑是我自己写驱动器时才发现的：`fix_e35_label` 会改 `simcore.py`，
    #    而自检第 3 项是**按 mtime 判新鲜度**的 ⇒ 残差对账必须排在它**之后**，
    #    否则链跑到最后第 3 项永远红，还会让人以为是标定漂了。
    if todo(0):
        # 2026-10-18 新增：工件头注释与 CATALOG 对齐（只改 docstring 一行，改前改后各跑一次
        # smoke 比 stdout ⇒ "注释改了、读数没变"是它自己证明的，不是我口头保证的）
        step('0', '工件头注释与 CATALOG 对齐（带读数不变证明）',
             [PY, 'sync_artifact_docstrings.py'], timeout=1800)
    if todo(1):
        step('1', '合并标定分片', [PY, 'merge_recal_shards.py'])
        n = count_jsonl(os.path.join(HERE, 'RECAL64_raw.jsonl'))
        assert n == 704, '合并后 %d 条，不是 704（= %d 题 × 11）' % (n, N_TASK_ALL)
        print('   RECAL64_raw.jsonl = %d 条（64 题 × 11）✓' % n, flush=True)
    if todo(2):
        assert os.path.exists(OLD_TAU), '旧 τ* 表副本不在归档里 ⇒ 会被覆盖且无法对账，先补副本'
        step('2', '重标 τ*/假阳率表', [PY, 'build_tables_v2.py'], timeout=600)
    if todo(3):
        # 这一步的 rc 一定是 0 或 1；1 不是错误，是"主矩阵要重跑"的结论 ⇒ 单独记，不当崩溃
        rc, out, tail = sh([PY, 'diff_tau_tables.py', OLD_TAU,
                            os.path.join(HERE, 'table_tau_v2.csv')])
        verdict = '主矩阵可续用' if rc == 0 else '主矩阵必须重跑'
        print('[步骤 3] τ* 换档判定 rc=%s ⇒ %s' % (rc, verdict), flush=True)
        log.write('步骤3 rc=%s verdict=%s\n%s\n' % (rc, verdict, '\n'.join(tail)))
        if rc not in (0, 1):
            raise SystemExit('diff_tau_tables 返回 %s：既不是 0 也不是 1 ⇒ 表结构变了，先修它' % rc)
    if todo(4):
        step('4', 'E35 改判写回标签源头（会改 simcore.py）', [PY, 'fix_e35_label.py'])
    if todo(5):
        # `check_benign.py` 是**续跑**型（按 (题,错型,seeds,horizon) 跳过已存在的行）。
        # 旧 BENIGN_PROOF.csv 是在**旧 τ*/旧引擎**上证的，续跑会一行都不干 ⇒ 第 6 项自检就成了
        # "拿上一轮的自证表给这一轮背书"。所以先把旧表改名归档，逼它整批重证（~20 分钟）。
        bp = os.path.join(HERE, 'BENIGN_PROOF.csv')
        if os.path.exists(bp):
            bak = os.path.join(HERE, '_archive_superseded',
                               'BENIGN_PROOF_pre_recal_%s.csv' % time.strftime('%m%d_%H%M'))
            os.rename(bp, bak)
            print('   旧自证表归档 → %s（本轮要在 τ* 重标后整批重证）' % os.path.basename(bak),
                  flush=True)
        out = step('5', '良性对照自证重建', [PY, 'check_benign.py'], timeout=3600)
        n = sum(1 for l in io.open(bp, encoding='utf-8')) - 1
        assert n >= 60, '重证后只有 %d 行 ⇒ 覆盖不全，别往下搬' % n
        print('   BENIGN_PROOF.csv = %d 行 ✓' % n, flush=True)
    if todo(6):
        # 2026-10-18 新增：stage1 必须在 J0 上线后整批重跑（`run_p0_crosscheck.py` 是**追加**写的，
        # 不先把旧表归档，就会把新旧两代混在一张 CSV 里 —— 那正是上一轮审计抓到的"半截产物"族）。
        p0 = os.path.join(HERE, 'P0_CROSSCHECK.csv')
        if os.path.exists(p0):
            bak = os.path.join(HERE, '_archive_superseded',
                               'P0_CROSSCHECK_preJ0_%s.csv' % time.strftime('%m%d_%H%M'))
            os.rename(p0, bak)
            print('   旧 stage1 表归档 → %s（本轮要在含 J0 的引擎上整批重跑）'
                  % os.path.basename(bak), flush=True)
        # 超时给到 2 小时：10-18 这次 stage1 实际跑完了（1082 行、64/64 题、无半行、无重复键），
        # 但中途电脑合盖暂停，墙钟时间超过原来的 3000s ⇒ 看门狗把已完成的子进程杀掉、整条链停在这里。
        # 这不是判据失败，是**时长假设**失败；`run_p0_crosscheck.py` 可续跑，所以重跑不重复计数。
        out = step('6', 'stage1 门禁整批重跑（含 J0 行）', [PY, 'run_p0_crosscheck.py'],
                   timeout=7200)
        n = sum(1 for l in io.open(p0, encoding='utf-8')) - 1
        n_j0 = sum(1 for l in io.open(p0, encoding='utf-8') if ',J0,' in l)
        assert n_j0 > 0, 'stage1 重跑完了却一行 J0 都没有 ⇒ 锚没接进生产路，别往下搬'
        print('   P0_CROSSCHECK.csv = %d 行，其中 J0 %d 行 ✓' % (n, n_j0), flush=True)
    if todo(7):
        step('7', '标定残差对账（要求 0 DRIFT，且必须晚于一切源文件改动）',
             [PY, 'check_recal_currency.py'], timeout=3000)
    if todo(8):
        step('8', '主表正式汇总', [PY, 'summarize_matrix_v2.py',
                                   'MUTANT_MATRIX_R10b.shard*.csv'])
    if todo(9):
        step('9a', '闸的负样本复验', [PY, 'neg_test_selfcheck.py'], timeout=3600)
        step('9b', '全项自检（条数以 SELFCHECK.md 为准，不在这里写死）', [PY, 'selfcheck_all.py'])
    if todo(10):
        step('10', '字段契约重建（含 trig_ 键 + 出生活闸）', [PY, 'build_field_contract.py'],
             timeout=3000)
        step('10b', '契约两条闸的负样本复验', [PY, 'check_contract_gates.py'])
    msg = '链跑完，用时 %.1f 分钟' % ((time.time() - t0) / 60.0)
    print(msg, flush=True)
    log.write('==== %s ====\n' % msg)
    log.close()


if __name__ == '__main__':
    main()
