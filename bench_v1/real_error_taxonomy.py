r"""腿 B 的**真实错型目录**：在人读定性的基础上，用可复算的检测器给 192 件分类计数。

为什么要它：论文现在有两份错型名单——腿 A 那份是**我注入的**（`simcore.py` 的错型表，186/186 按它计分），
腿 B 这份是**模型自己犯的**。一个自然的质疑是"你造的错算真错吗"，唯一诚实的答法是把两份名单摆一起对，
而不是嘴上说"覆盖了常见错型"。这张表就是"模型自己犯的"那一半。

⚠ 方法的边界（必须跟着数一起报）：
  · 检测器是**逐行文本判据**，不是语义分析 ⇒ 每类都有假阳/假阴风险。所以报数时同时给人读对照表，
    并在正文里写成"模式计数（approximate）"，不许写成"错误率"。
  · 一条都没命中的件 ≠ 没毛病，只等于这六种写法没出现 ⇒ 单列"未归类 N 件"。
  · **本脚本不参与打分**：只读源码，绝不进 τ\* 或主表（判分出口仍是 `criteria.run_artifact` + `cells()`）。

用法：~/miniconda3/python.exe real_error_taxonomy.py [工件目录]
输出：REAL_ERROR_TAXONOMY.md
"""
import io
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

HUMAN = {    # 本轮人读结论（读到行级的 4 件是硬结论，partial 的没定到行）
    'mh2-01__d3.py': ('真错(行级)', 'rem 不递减(:51) + wait_area 恒 0(:84/:88) + 分子全期分母预热后(:89)'),
    'md1-01__d2.py': ('真错(类级)', 'W 由 Little 反推(:103) 未独立测量；2.64× 说明 L 或离开率计数也错'),
    'mm1-03__d2.py': ('真错(类级)', 'p_wait 报 0.0005 vs 真值 0.6：触发条件几乎不成立，计数定义与题面不一致'),
    'jackson2-06__d2.py': ('小偏差超阈值', 'L 1.017×（τ*=1%），面积有 warm 守卫 ⇒ 疑预热窗口不足/未收敛，非结构错'),
    'eoq-01__d1.py': ('全一致(对照)', '闭式 EOQ，3 抽逐位一致'),
    'jackson2-08__d2.py': ('全一致(对照)', '—'),
    'mmc-01__d2.py': ('全一致(对照)', '—'),
    'md1-01__d1.py': ('partial', 'L 1.23× 且 busy_frac 报 0，未读到行级'),
    'mh2-01__d1.py': ('partial', 'L 报 0，未读到行级'),
    'mh2-01__d2.py': ('partial', 'L 0.58×，未读到行级'),
    'mm1-02__d1.py': ('partial', 'p_wait 报 0，未读到行级'),
}


def d_wittle(s):
    """W 不是测出来的，是 `W = L / ...` 反推的 ⇒ 与 J2a 同源，自己验自己。"""
    return bool(re.search(r'^\s*W *= *L[ /*]', s, re.M))


def d_rem(s):
    """服务剩余时间 `rem` 用 `t + rem` 比较却从不递减 ⇒ 每来一个事件就把完成时刻重新起算，
    服务台永远做不完（实测 `mh2-01__d3` 的 L=36002 就是这么来的）。"""
    return bool(re.search(r't *\+ *rem\b', s)) and not re.search(r'\brem *-=|\brem *= *rem *-|end_svc', s)


def d_waitzero(s):
    """等待面积只写 `+= 0.0` 占位 ⇒ W 必为 0。"""
    return bool(re.search(r'wait_area *\+= *0\.0', s))


def d_warm(s):
    """分母**确实**是预热后窗口（`L = area / win` 或 `L = area / (H - warm)`），但**存在**至少一条
    `area +=` 前面 3 行没有 warm 守卫 ⇒ 分子全期、分母稳态窗口，L 系统性偏高。

    ⚠ 留痕（第二次修检测器，同样是先给人读对照才发现）：第一版只看"文件里出现过 `win = H - warm`"
    就断定分母是稳态窗口。被全一致对照组 `jackson2-08__d2.py` 打脸——它第 120 行是 `L = area / H`，
    那个 `win` 只是往契约字段里报的数，没参与除法 ⇒ 假阳。所以判据改成"必须看见 L 的除法本身"。
    """
    if not re.search(r'^\s*L *= *(?:tot_)?area *[/\\] *(?:win|H *- *warm)\b', s, re.M):
        return False
    lines = s.splitlines()
    for i, l in enumerate(lines):
        if re.search(r'\b(?:area|tot_area) *\+=', l):
            ctx = '\n'.join(lines[max(0, i - 3):i])
            if 'warm' not in ctx:
                return True
    return False


def d_rateswap(s):
    """`random.expovariate(x)` 要的是**率** λ，传均值 m 就等于把服务时间变成 1/m²。
    这里只抓"直接把变量名当率传且该名字像均值（mean/s1/s2/r?）"这一种写法。"""
    return bool(re.search(r'expovariate\(\s*(?:mean|mean_s|s1|s2|r1|r2)\s*\)', s))


def d_noop(s):
    r"""**真**无操作：`x = x`（整行右端就是左端本身），或 `x = y if C else y`（两分支同值 ⇒ 条件白写）。

    ⚠ 留痕：第一版这里写成 `([a-z_]\w*) *= *\1\b`，于是 `h = h * 1.2`、`queue = queue + 1` 这种
    **正常累加**全被判成无操作赋值，命中 128/192 = 66.7% —— 一台假阳机器。是看"它到底匹配了哪些行"
    才抓出来的（变量名频次 top 是 queue/rem/t，一看就不是占位赋值）。修规则同 `rem` 那条：
    模式计数在没被人读对照之前不许进正文。
    """
    if re.search(r'^\s*([a-z_]\w*) *= *\1\s*$', s, re.M):
        return True
    return bool(re.search(r'^\s*[a-z_]\w* *= *([a-z_]\w*) +if +[^:\n]+ +else +\1\s*$', s, re.M))


DETECT = [
    ('W_not_measured', d_wittle, 'W 由 Little 定律从 L 反推，未独立测量 ⇒ 与 J2a 同一来源，'
     '"等待时间算错"这一族**仪器检不出来**（自己验自己）'),
    ('rem_not_decremented', d_rem, '服务剩余时间不递减 ⇒ 队列发散、L 爆大（真实成因，不是单位问题）'),
    ('wait_area_zero_only', d_waitzero, '等待面积只 `+= 0.0` 占位 ⇒ W 必报 0'),
    ('warm_numerator_mismatch', d_warm, '分子全期累加 / 分母只用预热后窗口 ⇒ L 系统性偏高'),
    ('rate_mean_swap', d_rateswap, '`expovariate()` 传成均值 ⇒ 服务时间差 (均值)² 倍，稳定性都可能反过来'),
    ('noop_assignment', d_noop, '无操作赋值/三元式 ⇒ 半成品逻辑信号（不直接改数值，但与上面几类共现）'),
]


def strip_comments(s):
    """粗剥散文：模块级 docstring、整行注释、行尾注释。只做"别让散文冒充代码"，
    不做完整语法分析（本两批语料里没有含 `#` 的字符串字面量；有的话这里会过切，
    宁可过切也不要漏切——过切只会少判，漏切会造假阳）。"""
    out, in_doc, quote = [], False, None
    for ln in s.splitlines():
        st = ln.strip()
        if in_doc:
            if quote in ln:
                in_doc = False
            continue
        if st.startswith('#'):
            continue
        if st[:3] in ('"""', "'''"):
            quote = st[:3]
            if st.count(quote) >= 2:
                continue                      # 单行 docstring，整行丢掉
            in_doc = True
            continue
        cut = ln.find('#')
        if cut >= 0:
            ln = ln[:cut]
        out.append(ln)
    return '\n'.join(out)


def scan(d, strip_prose=False):
    """strip_prose=True 时先剥掉模块 docstring 与注释行，只扫**代码**。
    为什么要有这个开关（2026-10-18 实测出来的）：注入语料的工件是薄壳，
    我把真实标本的代码（`rem`、`wait_area += 0.0`、`W = L/…`）原样引用进 docstring 当出处，
    于是不剥注释的口径在注入语料上命中 14/408 —— 一台我自己造的假阳机器。"""
    files = sorted(f for f in os.listdir(d) if f.endswith('.py') and '__REF' not in f)
    hit, per_file = defaultdict(list), {}
    for f in files:
        s = io.open(os.path.join(d, f), encoding='utf-8', errors='replace').read()
        if strip_prose:
            s = strip_comments(s)
        got = [name for name, fn, _ in DETECT if fn(s)]
        per_file[f] = got
        for name in got:
            hit[name].append(f)
    return files, hit, per_file


def main():
    dirs = sys.argv[1:] or [os.path.join(HERE, 'legB', 'flash20261018')]
    dirs = [x if os.path.isabs(x) else os.path.join(HERE, x) for x in dirs]
    res = {d: scan(d) for d in dirs}
    files, hit, per_file = res[dirs[0]]
    n = len(files)
    L = ['# 腿 B 真实错型目录（模式计数，主语料 `%s`，%d 件）'
         % (os.path.basename(dirs[0].rstrip('\\/')), n), '']
    L.append('> 这是"**模型自己犯的错**"那一半名单；腿 A 那份（186/186）是"我注入的错"。'
             '两份对齐才是"我造的错算真错吗"的答案。计数是**逐行文本判据**，不是语义分析 ⇒ 只能当'
             '错型目录，不能当错误率；且本脚本不参与任何打分。')
    L.append('')
    if len(dirs) > 1:
        res_s = {d: scan(d, strip_prose=True) for d in dirs}
        L.append('## 跨语料对照（这条决定本表能不能拿来跟注入名单比）')
        L.append('')
        L.append('两种口径都印：**连散文扫**（原始口径，历史数就是它）与**只扫代码**'
                 '（剥掉 docstring 与注释）。差值本身就是信息。')
        L.append('')
        L.append('| 语料 | 件数 | 命中 ≥1 种模式的件（连散文） | 占比 | 只扫代码 | 占比 |')
        L.append('|---|---|---|---|---|---|')
        for d in dirs:
            fs, h, pf = res[d]
            _fs, _h, pf_s = res_s[d]
            k = sum(1 for f in fs if pf[f])
            ks = sum(1 for f in fs if pf_s[f])
            L.append('| `%s` | %d | %d | %.1f%% | %d | %.1f%% |' % (
                os.path.basename(d.rstrip('\\/')), len(fs), k, 100.0 * k / len(fs) if fs else 0,
                ks, 100.0 * ks / len(fs) if fs else 0))
        L.append('')
        L.append('⚠ **写法特定**：六个模式的关键词（`rem`、`wait_area`、`win = H - warm`、`W = L/…`）'
                 '是 flash 那批的写法。第二行那类语料命中率如果接近 0，**不能**读成"那批工件没有这些毛病"，'
                 '只能读成"同一毛病换个写法就检不出" ⇒ 所以本表**只用于描述腿 B 语料**，'
                 '与注入错型名单的对齐要靠"错在哪一环节"的语义映射，不能靠这套正则。')
        L.append('')
        L.append('⚠ **这台假阳机器是我自己造的（2026-10-18）**：注入语料的工件是薄壳，'
                 '我把真实标本的代码原样写进 docstring 当出处，于是"连散文扫"的口径在注入语料上'
                 '命中了 %d/%d 件。只扫代码之后回到 %d/%d 件。'
                 '教训：**出处引用与判据扫描不能共用同一段文本**，否则我把要检的东西写进了被检的对象里。'
                 % (sum(1 for f in res[dirs[-1]][0] if res[dirs[-1]][2][f]), len(res[dirs[-1]][0]),
                    sum(1 for f in res_s[dirs[-1]][0] if res_s[dirs[-1]][2][f]),
                    len(res_s[dirs[-1]][0])))
        L.append('')
    L.append('| 模式 | 命中件 | 占全批 | 为什么这类会让判据失准 / 造成哪个观测量偏 |')
    L.append('|---|---|---|---|')
    for name, _fn, why in DETECT:
        k = len(hit.get(name, []))
        L.append('| `%s` | %d | %.1f%% | %s |' % (name, k, 100.0 * k / n, why))
    uncl = [f for f in files if not per_file[f]]
    multi = [f for f in files if len(per_file[f]) >= 2]
    L.append('')
    L.append('- 六种模式**一条都没命中**：%d/%d = %.1f%%（不等于没毛病，只等于这六种写法没出现）'
             % (len(uncl), n, 100.0 * len(uncl) / n))
    L.append('- 同时命中 ≥2 种：%d 件（多因叠加；主表里一个报警格可能对应多个成因，'
             '所以本表不与报警格一一对应）' % len(multi))
    L.append('')
    L.append('## 与人读样本的对照（看检测器有没有漏、有没有冤枉对照组）')
    L.append('')
    L.append('| 件 | 人读结论 | 人读依据（到行） | 检测器命中 | 判定 |')
    L.append('|---|---|---|---|---|')
    for f in sorted(HUMAN):
        verdict, why = HUMAN[f]
        got = per_file.get(f, [])
        if not got:
            tag = '漏报' if verdict.startswith('真错') else '—'
        elif verdict.startswith('全一致'):
            tag = '**疑假阳**（对照组被抓到，要么检测器太松，要么它确实有毛病但数值仍对）'
        else:
            tag = '抓到'
        L.append('| `%s` | %s | %s | %s | %s |' % (f, verdict, why, ','.join(got) or '-', tag))
    L.append('')
    L.append('## 下一步（这张表现在只是目录，还不是结论）')
    L.append('')
    L.append('1. 把六个模式与 `simcore.py` 的注入错型表**映到同一坐标**（服务时间分布 / 等待计量 / '
             '预热口径 / 率与均值 / 事件调度 / 守恒），报"注入名单里有而真实没有"与"真实有而注入名单里没有"；')
    L.append('2. 人读样本从 8 件扩到每模板 ≥2 件（当前 4 个模板只到 partial）；')
    L.append('3. `W_not_measured` 那一族要单独处理：它意味着**J2a 对这些工件是恒真的**，'
             '属于"仪器盲区"而不是"模型错"，必须进 §能力边界表。')
    out = os.path.join(HERE, 'REAL_ERROR_TAXONOMY.md')
    io.open(out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    sys.stdout.buffer.write(('files=%d unclassified=%d multi=%d -> %s\n' % (
        n, len(uncl), len(multi), os.path.basename(out))).encode('utf-8', 'replace'))


if __name__ == '__main__':
    main()
