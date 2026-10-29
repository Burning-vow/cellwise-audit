"""给外部题集那两个"只有参照件"的库存题补变异件。

为什么它们之前是空的：build_external_artifacts.py 的 `REP_TYPES` 只有 9 个码
（E01/E02/E03/E24/E04/E25/E14/E21/E43），全是排队/估计侧的，
`if tpl not in CATALOG[et]['applies']` 对 eoq/newsvendor 全部不成立 ⇒ 0 件。
跑分器本身**早就支持库存观测量**（`from inv_obs import j1_inv`），所以缺的不是能力，是清单。

补的码（从 simcore.CATALOG 现读 applies 含 eoq/newsvendor 的）：
  eoq: E35 E36 E37 E38 E42  |  newsvendor: E31 E32 E33 E34
  —— 8 个 detectable + 1 个 weak（E42）。
  **不加良性对照**：外部集本来就没有良性件，别在这里悄悄换设计。

验收硬指标（不是"跑通了"）：
  1) 旧 77 行 (task_id, error_type) 集合**一格不少、一格不多**地还在；
  2) 新 9 行落在两个库存题上，12/12 题都有变异件；
  3) 每条新工件的 verdict 与 CATALOG 声明对得上，对不上就照实报，不改声明凑数。
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, 'build_external_artifacts.py')
MUTS = os.path.join(HERE, 'external_mutants.jsonl')
TASKS = os.path.join(HERE, 'external_tasks.jsonl')
SIM = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'simcore.py')
STAMP = 'pre_inv_2026-10-21'

# ---- 0) 从 CATALOG 现读适用码，不手抄 ----
s = io.open(SIM, encoding='utf-8').read()
applies = {}
for m in re.finditer(r"^\s*'(E\d{2})':\s*dict\((.*?)\),\s*$", s, re.M | re.S):
    a = re.search(r'applies=\(([^)]*)\)', m.group(2))
    applies[m.group(1)] = [x.strip().strip("'") for x in a.group(1).split(',')] if a else []
BENIGN = {'E26', 'E28', 'E29', 'E30'}
inv_codes = sorted(k for k, v in applies.items()
                   if ('eoq' in v or 'newsvendor' in v) and k not in BENIGN)
assert inv_codes == ['E31', 'E32', 'E33', 'E34', 'E35', 'E36', 'E37', 'E38', 'E42'], \
    '适用码清单与我以为的不一样：%s' % inv_codes
print('CATALOG 现读：库存适用非良性码 %d 个 = %s' % (len(inv_codes), inv_codes))

OLD = [json.loads(l) for l in io.open(MUTS, encoding='utf-8') if l.strip()]
old_keys = sorted((r['task_id'], r['error_type']) for r in OLD)
print('补之前：mutants=%d 覆盖 %d 题' % (len(OLD), len({r['task_id'] for r in OLD})))

# ---- 1) 补构建器 ----
for p in (BUILD, MUTS):
    if not os.path.exists(p + '.' + STAMP):
        shutil.copyfile(p, p + '.' + STAMP)
b = io.open(BUILD, encoding='utf-8').read()
OLD_LINE = "REP_TYPES = ('E01', 'E02', 'E03', 'E24', 'E04', 'E25', 'E14', 'E21', 'E43')"
NEW_LINE = ("REP_TYPES = ('E01', 'E02', 'E03', 'E24', 'E04', 'E25', 'E14', 'E21', 'E43')\n"
            "# 库存侧代表码：2026-10-21 补，之前外部集 12 题里 eoq/newsvendor 两题只有参照件。\n"
            "INV_TYPES = %r" % (tuple(inv_codes),))
assert b.count(OLD_LINE) == 1, 'REP_TYPES 行没找到原样'
b = b.replace(OLD_LINE, NEW_LINE)
assert b.count('for et in REP_TYPES:') == 1
b = b.replace('for et in REP_TYPES:', 'for et in REP_TYPES + INV_TYPES:')
io.open(BUILD + '.tmp', 'w', encoding='utf-8', newline='\n').write(b)
os.replace(BUILD + '.tmp', BUILD)
r = subprocess.run([sys.executable, '-m', 'py_compile', BUILD], capture_output=True)
assert r.returncode == 0, r.stderr.decode('utf-8', 'replace')[-400:]
print('builder patched (REP_TYPES + INV_TYPES), compiles')

# ---- 2) 重建（幂等：已存在的工件文件跳过）----
r = subprocess.run([sys.executable, BUILD], cwd=HERE, capture_output=True,
                   env=dict(os.environ, PYTHONIOENCODING='utf-8'))
print(r.stdout.decode('utf-8', 'replace')[-300:])
if r.returncode:
    print(r.stderr.decode('utf-8', 'replace')[-600:])
    shutil.copyfile(BUILD + '.' + STAMP, BUILD)
    shutil.copyfile(MUTS + '.' + STAMP, MUTS)
    sys.exit(1)

new = [json.loads(l) for l in io.open(MUTS, encoding='utf-8') if l.strip()]
new_keys = sorted((x['task_id'], x['error_type']) for x in new)
lost = [k for k in old_keys if k not in set(new_keys)]
added = [k for k in new_keys if k not in set(old_keys)]
ntask = len({x['task_id'] for x in new})
print('补之后：mutants=%d 覆盖 %d 题；旧行丢失 %d；新增 %d' % (len(new), ntask, len(lost), len(added)))
assert not lost, '旧行丢了：%s' % lost[:5]
assert len(added) == 9, '新增不是 9 件：%s' % added
assert ntask == 12, '覆盖题数不是 12：%d' % ntask
assert sorted({t for t, _ in added}) == ['ext-eoq-01', 'ext-newsvendor-01']
print('验收 1+2 通过：12/12 题都有变异件，旧 77 行一格没丢')

# ---- 3) 工件文件真的建出来了没有（"产物建了没接线"那一类）----
ART = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'artifacts_external')
missing = []
for t, e in added:
    fn = os.path.join(ART, '%s__%s.py' % (t, e))
    if not os.path.exists(fn):
        missing.append(os.path.basename(fn))
    else:
        txt = io.open(fn, encoding='utf-8').read()
        if "%s', '%s'" % (t, e) not in txt:
            missing.append('%s (入口里没有 main(%s,%s))' % (os.path.basename(fn), t, e))
assert not missing, '工件缺失：%s' % missing
print('验收 3：9 个新工件都在盘上且入口参数正确 -> %s' % ART)
