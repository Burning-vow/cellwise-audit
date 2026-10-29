"""给 c×K 扫描补 ρ=0.4 的控制点（条4 的严谨版），并修两处会在这一跑里咬人的东西。

改三处：
  1) build_cxk.GRID 加 (2,4,8,10)/(2,6,8,10)/(2,8,8,10) —— 第一格就是 mmcK-04 本身
     (c=2,K=4,λ=8,μ=10)，后两格是同一负载下的等待位升级，用来对齐其它负载的结构。
  2) run_cxk 的 §5 把"3 个 ρ"写死在正文句子里 ⇒ 加负载后那句自动变假。改成现算。
  3) run_cxk 用 open(...,'w') 直接盖 CXK_MATRIX.csv / CXK_SUMMARY.md。
     我 10-20 刚因为"杀掉一个非原子写的后台任务"把 64 行的权威表截成 12 行，
     这次同样要跑 30 分钟 ⇒ 一律 .tmp + os.replace。

跑完的验收不是"新点跑出来了"，而是**旧 17 题的判定一格都没动**；动了就说明加题本身
改变了结果，那这条控制点也不能用。
"""
import io
import os
import re
import shutil
import subprocess
import sys

CXK = os.path.dirname(os.path.abspath(__file__))   # 本脚本就放在 cxk/ 里，不要再往上剥两层
STAMP = 'pre_rho04_2026-10-20'

BUILD = os.path.join(CXK, 'build_cxk.py')
RUN = os.path.join(CXK, 'run_cxk.py')

OLD_GRID = """    (2, 4, 8, 5),    # rho=0.8 control (same cell as mmcK-03)
"""
NEW_GRID = """    (2, 4, 8, 5),    # rho=0.8 control (same cell as mmcK-03)
    (2, 4, 8, 10),   # rho=0.4 control (same cell as mmcK-04), added 2026-10-20
    (2, 6, 8, 10),   # rho=0.4, K=6
    (2, 8, 8, 10),   # rho=0.4, K=8
"""

OLD_HARD = '''    lines.append(f"- c=2,K=4 共 {len(control)} 个格（3 个 ρ × 2 错型 × 2 观测量）。")'''
NEW_HARD = '''    nrho = len({r["rho"] for r in control})
    lines.append(f"- c=2,K=4 共 {len(control)} 个格（现算 {nrho} 个 ρ × 2 错型 × 2 观测量；"
                 f"ρ={sorted({r['rho'] for r in control})}）。")'''

OLD_CSVW = '''    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)'''
NEW_CSVW = '''    tmp = str(OUT_CSV) + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    os.replace(tmp, OUT_CSV)   # 半份矩阵比没有矩阵更坏：它看起来像证据'''

OLD_MDW = '''    OUT_MD.write_text("\\n".join(lines), encoding="utf-8")'''
NEW_MDW = '''    _tmp = str(OUT_MD) + ".tmp"
    with open(_tmp, "w", encoding="utf-8") as f:
        f.write("\\n".join(lines))
    os.replace(_tmp, OUT_MD)'''

EDITS = [(BUILD, OLD_GRID, NEW_GRID), (RUN, OLD_HARD, NEW_HARD),
         (RUN, OLD_CSVW, NEW_CSVW), (RUN, OLD_MDW, NEW_MDW)]

for p in (BUILD, RUN):
    shutil.copyfile(p, p + '.' + STAMP)
for name in ('tasks_cxk.jsonl', 'CXK_GRID.csv', 'CXK_MATRIX.csv', 'CXK_SUMMARY.md'):
    src = os.path.join(CXK, name)
    if os.path.exists(src):
        shutil.copyfile(src, src + '.' + STAMP)
print('backups written with suffix .%s' % STAMP)

cur = {}
for path, old, new in EDITS:
    if path not in cur:
        cur[path] = io.open(path, encoding='utf-8').read()
    n = cur[path].count(old)
    if n != 1:
        print('ABORT: pattern %dx in %s' % (n, os.path.basename(path)))
        print('  head: %s' % old.splitlines()[0][:70])
        for p in cur:
            shutil.copyfile(p + '.' + STAMP, p)
        sys.exit(1)
    cur[path] = cur[path].replace(old, new)

# run_cxk.py 需要 import os 才谈得上 os.replace —— 先确认它在，不在就补
if 'import os' not in cur[RUN]:
    cur[RUN] = cur[RUN].replace('import csv\n', 'import csv\nimport os\n', 1)
    print('added `import os` to run_cxk.py')

for path, text in cur.items():
    io.open(path + '.tmp', 'w', encoding='utf-8', newline='\n').write(text)
    os.replace(path + '.tmp', path)
    back = io.open(path, encoding='utf-8').read()
    assert back == text, 'readback differs: %s' % path
print('patched %d file(s), readback ok' % len(cur))

# 语法闸：py_compile 过不代表跑过，但至少不引入低级断行错
for path in cur:
    r = subprocess.run([sys.executable, '-m', 'py_compile', path], capture_output=True)
    print('py_compile %s rc=%d %s' % (os.path.basename(path), r.returncode,
                                      r.stderr.decode('utf-8', 'replace')[-200:]))
    if r.returncode:
        for p in cur:
            shutil.copyfile(p + '.' + STAMP, p)
        sys.exit(1)
