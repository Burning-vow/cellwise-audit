"""把工件头部的 `theory_ref=` 那一行与 `simcore.CATALOG` 对齐，并**证明改动没动读数**。

为什么要有它（2026-10-18）：工件文件是给腿 B 当"被审判对象"的，它们的头部注释也是论文里
"这件是什么错型、理论上该谁抓"的**可指认载体**。10-17 改 E28/E35 的写法时只改了 `mutants.jsonl`
与 `simcore.py`，14 件 `__e28.py` 与 6 件 `__e35.py` 的头注释里还留着旧句子
（"W 必须回乘而工件没回乘 ⇒ J1-W 报警"），而矩阵里 `mm1-02__E28` 的 J1|W rel=1.1e-3 根本没报警
⇒ 注释与读数互相打脸。这属于本仓反复出现的"正文/注释与代码定义漂移"，不能留。

安全做法：
  1) 只替换 docstring 里以 `theory_ref=` 开头的那一行，代码一行不碰；
  2) 替换**之前**先把每件跑一次（`--seeds 3 --horizon 5000`，smoke 口径）存下 stdout，
     替换**之后**再跑一次，逐字节比 ⇒ 读数必须完全相同（同种子同窗口）；
  3) 任何一件比出不一样，立刻把它的文件还原并停下（改动是可逆的，备份在 temp）。
"""
import io
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import simcore as SC   # noqa: E402

ART = os.path.join(HERE, 'artifacts')
PY = sys.executable or os.path.expanduser('~/miniconda3/python.exe')
CODES = None      # 10-19 改：原来写死 ('E28','E35')（历史上漂移过的那两类），
                  # 于是新算子改了 expected 时它根本不看 ⇒ 覆盖面从"两类"扩到"CATALOG 全类"。
                  # 命令行可传子集：`sync_artifact_docstrings.py E28 E35`。
SMOKE = ['--seeds', '3', '--horizon', '5000']


def run_stdout(path):
    p = subprocess.run([PY, path] + SMOKE, cwd=HERE, capture_output=True,
                       text=True, encoding='utf-8', errors='replace')
    assert p.returncode == 0, 'smoke 跑失败 %s：%s' % (path, (p.stderr or '')[-200:])
    return p.stdout


def main():
    d = tempfile.mkdtemp(prefix='docsync_')
    codes = tuple(a.upper() for a in sys.argv[1:]) or tuple(sorted(SC.CATALOG))
    TPL = {t['task_id']: t['template'] for t in SC.load_tasks()}
    targets = []
    for fn in sorted(os.listdir(ART)):
        if not fn.endswith('.py') or '__' not in fn:
            continue
        code = fn.rsplit('__', 1)[1][:-3].upper()
        if code in codes:
            targets.append((fn, code))
    assert targets, 'artifacts 里找不到 %s 的工件 ⇒ 目录不对，停' % (codes,)
    changed, same, bad = [], [], []
    for fn, code in targets:
        p = os.path.join(ART, fn)
        src = io.open(p, encoding='utf-8').read()
        want = SC.CATALOG[code]['theory_ref']
        m = re.search(r'^theory_ref=.*$', src, re.M)
        if not m:
            bad.append((fn, '头注释里没有 theory_ref 行'))
            continue
        new = src[:m.start()] + 'theory_ref=' + want + src[m.end():]
        # ⚠ 10-19 补：本工具原来只对齐 `theory_ref=`，于是 CATALOG 改了 `expected`
        #    （E40 的 mm1K 两题由 detectable 改 blind）时，工件头里的 `expected=` 会留着旧值而本工具报"已一致"。
        #    同一行注释里有两个权威字段，只核一个等于半个门禁 ⇒ 现在两个都对齐。
        m2 = re.search(r'^(family=\S+\s+expected=)(\w+)', new, re.M)
        if m2:
            tid = fn.split('__')[0]
            cat = SC.CATALOG[code]
            wexp = cat.get('expected_by_tpl', {}).get(TPL.get(tid, ''), cat['expected'])
            new = new[:m2.start(2)] + wexp + new[m2.end(2):]
        if new == src:
            same.append(fn)
            continue          # 没漂移就不跑 smoke：472 件 ×2 次进程是白烧的机时
        before = run_stdout(p)                       # 改动前的读数（同种子同窗口）
        bak = os.path.join(d, fn)
        io.open(bak, 'w', encoding='utf-8').write(src)
        io.open(p, 'w', encoding='utf-8').write(new)
        changed.append(fn)
        after = run_stdout(p)                        # 改动后的读数
        if after != before:
            if os.path.exists(bak):
                io.open(p, 'w', encoding='utf-8').write(io.open(bak, encoding='utf-8').read())
            bad.append((fn, '改注释后读数变了 ⇒ 已还原'))
    print('[docsync] 目标 %d 件：改动 %d、已一致 %d、异常 %d' % (
        len(targets), len(changed), len(same), len(bad)))
    for b in bad:
        print('  FAIL', b)
    print('备份在 %s（只留异常件才需要人工看，正常情况改动只在注释行）' % d)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
