"""字段契约那三条闸的**负样本复验**（规矩：新闸不放一个坏样本进去，就不算建了闸）。

全部在 temp 目录的**合成副本**上做，交付物一根手指都不碰；用 `SC_TAU_CSV` / `SC_CONTRACT_CSV`
两个环境变量把合成文件喂进 `legB_grade`（这就是那两个口子存在的理由）。

要复验的三条（都来自外部审计第二轮 F-6）：
  G1 τ* 表里有一行标了参照件根本不报的统计量（`mm1 / rho`）⇒ 必须响亮停下，不许静默少比一个观测量；
  G2 契约里冒出一个清单外的仪器键（`trig_newthing`）⇒ 必须停下；
  G3 正向对照：真文件下 64 题全部通过，且 `trig_*` 一个都不进 required/optional。
"""
import csv
import io
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
TAU = os.path.join(HERE, 'table_tau_v2.csv')
CON = os.path.join(HERE, 'field_contract.csv')

CHILD = r'''
import os, sys
sys.path.insert(0, r'%s')
import criteria as C, legB_grade as LG
t = [x for x in C.load_tasks() if x['task_id'] == sys.argv[1]][0]
try:
    r, o = LG.contract_fields(t, 'neg-test')
except BaseException as e:
    print('FIRED %%s: %%s' %% (type(e).__name__, str(e)[:200]))
    sys.exit(7)
print('SILENT required=%%s optional=%%s' %% (r, o))
sys.exit(0)
''' % HERE


def run(task_id, tau_csv, con_csv):
    env = dict(os.environ, SC_TAU_CSV=tau_csv, SC_CONTRACT_CSV=con_csv,
               PYTHONIOENCODING='utf-8')
    d = tempfile.mkdtemp(prefix='negc_')
    child = os.path.join(d, 'child.py')
    io.open(child, 'w', encoding='utf-8').write(CHILD)
    p = subprocess.run([PY, child, task_id], capture_output=True, text=True,
                       encoding='utf-8', env=env)
    return p.returncode, (p.stdout or '').strip().splitlines()[-1:] or ['(无输出)']


def main():
    out = []
    # G1：往 τ* 表塞一行 mm1/rho（参照件不报 rho，τ* 表里也没有 rho）
    tmp_tau = os.path.join(tempfile.gettempdir(), 'neg_tau_with_rho.csv')
    rows = list(csv.DictReader(io.open(TAU, encoding='utf-8')))
    fake = dict(rows[0])
    fake.update(criterion='J1', statistic='rho', template='mm1', tau_star='0.010')
    rows.append(fake)
    with io.open(tmp_tau, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    rc, msg = run('mm1-01', tmp_tau, CON)
    out.append(('G1 τ* 表有参照件不报的统计量（mm1/rho）', rc == 7, msg[0]))

    # G2：契约里塞一个清单外的仪器键
    tmp_con = os.path.join(tempfile.gettempdir(), 'neg_contract_trigX.csv')
    crows = list(csv.DictReader(io.open(CON, encoding='utf-8')))
    for r in crows:
        if r['task_id'] == 'mm1-01':
            r['keys'] = r['keys'] + ' trig_newthing'
    with io.open(tmp_con, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(crows[0].keys()))
        w.writeheader()
        for r in crows:
            w.writerow(r)
    rc, msg = run('mm1-01', TAU, tmp_con)
    out.append(('G2 契约冒出清单外的仪器键（trig_newthing）', rc == 7, msg[0]))

    # G3：正向对照——真文件全过，且仪器键不外泄
    import criteria as C
    import legB_grade as LG
    taus = LG.tau_map()
    bad, nfire = [], 0
    for t in C.load_tasks():
        try:
            r, o = LG.contract_fields(t, 'positive', taus)
        except BaseException as e:                          # noqa: BLE001
            nfire += 1
            bad.append('%s: %r' % (t['task_id'], e))
            continue
        leak = [k for k in r + o if k.startswith('trig_')]
        if leak:
            bad.append('%s 把仪器键铺进了 prompt：%s' % (t['task_id'], leak))
    out.append(('G3 正向对照：64 题全过且 trig_* 不外泄', not bad and not nfire,
                '触发 %d 题；违规 %s' % (nfire, bad[:3] or '无')))

    lines = ['# 字段契约闸的负样本复验（`check_contract_gates.py` 产生）', '']
    for name, ok, msg in out:
        lines.append('- %s **%s** — %s' % ('PASS' if ok else 'FAIL', name, msg))
    txt = '\n'.join(lines) + '\n'
    io.open(os.path.join(HERE, 'CONTRACT_GATES.md'), 'w', encoding='utf-8').write(txt)
    sys.stdout.buffer.write(txt.encode('utf-8'))
    return 0 if all(ok for _, ok, _ in out) else 1


if __name__ == '__main__':
    sys.exit(main())
