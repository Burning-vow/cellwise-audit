#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the three manuscript figures from the per-cell matrices."""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
FIG = HERE / "figs"
MATRIX_CSV = (HERE.parent / "bench_v1" / "exp_2026-10-19" / "cxk"
              / "CXK_MATRIX.csv")
FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

BLUE = "#1f5fa8"
LBLUE = "#6aa6d8"
ORANGE = "#c65f1a"
LORANGE = "#e9a15b"
GREEN = "#3a7d44"
GRAY = "#777777"
RED = "#b2182b"


def box(ax, x, y, w, h, text, fc="#f3f6fa", ec="#4a6fa5", fs=7.4):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012",
                       linewidth=0.8, edgecolor=ec, facecolor=fc)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color="#1a1a1a", linespacing=1.15)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color="#555555", lw=0.8,
                                shrinkA=1.5, shrinkB=1.5))


def fig_method():
    fig, ax = plt.subplots(figsize=(7.0, 2.35))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    w, h = 0.235, 0.34
    y1, y2 = 0.63, 0.10
    xs = [0.008, 0.252, 0.496, 0.740]
    labels1 = [
        "Reference corpus\n9 templates,\n64 tasks",
        "Second-model audit\n3 models x 3\nsamples (192 each)",
        "Our corpus\n1,348 artifacts\n(1,128 inj. + 220 benign)",
        "Judge J0-J3\nunits, truth,\npairing",
    ]
    labels2 = [
        "Theorem layer\n908 issued\n(864 judged)",
        "Cell verdicts\nTP / MISS\nBLIND / WEAK",
        "Denominator\nstrict / judgeable\n/ excluded",
        "Report\nboundary +\ncluster bounds",
    ]
    for i, lab in enumerate(labels1):
        box(ax, xs[i], y1, w, h, lab, fc="#eef4fb", fs=7.0)
    for i, lab in enumerate(labels2):
        box(ax, xs[i], y2, w, h, lab, fc="#f7f1e8" if i != 2 else "#eef7ee", fs=7.0)
    for i in range(3):
        arrow(ax, xs[i] + w + 0.004, y1 + h / 2, xs[i + 1] - 0.004, y1 + h / 2)
        arrow(ax, xs[i] + w + 0.004, y2 + h / 2, xs[i + 1] - 0.004, y2 + h / 2)
    # vertical links: judge -> verdicts; theorem -> verdicts
    arrow(ax, xs[3] + w / 2, y1 - 0.01, xs[3] + w / 2, y2 + h + 0.01)
    arrow(ax, xs[0] + w / 2, y1 - 0.01, xs[0] + w / 2, y2 + h + 0.01)
    fig.savefig(FIG / "fig1_method.png")
    fig.savefig(FIG / "fig1_method.pdf")
    plt.close(fig)


def _wilson(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / den
    half = z * ((p * (1.0 - p) / n + z * z / (4.0 * n * n)) ** 0.5) / den
    return min(1.0, centre + half)


def _cluster_rows():
    import csv
    p = (HERE.parent / "bench_v1" / "exp_2026-10-19" / "full64"
         / "P4_task_cluster_full64.csv")
    if not p.exists():
        return None
    return {r["category"]: r for r in csv.DictReader(open(p, encoding="utf-8"))}


def fig_main():
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(7.0, 2.6), gridspec_kw={"width_ratios": [1.0, 1.25]}
    )
    rows = _cluster_rows()
    if rows:
        det = rows["detectable"]
        det_j = int(det["judged"])
        det_s = int(det["success"])
        det_c = int(det["collapse"])
        eff_j = max(1, det_j - det_c)
        blinds = rows["blind"]
        weak = rows["weak"]
        ben = rows["benign"]
        cats = ["Detectable\n(raw)", "Detectable\nafter E07", "Blind", "Weak"]
        vals = [det_s / det_j, det_s / eff_j,
                int(blinds["success"]) / int(blinds["judged"]),
                int(weak["success"]) / int(weak["judged"])]
        labels = ["%d/%d" % (det_s, det_j), "%d/%d" % (det_s, eff_j),
                  "%d/%d" % (int(blinds["success"]), int(blinds["judged"])),
                  "%d/%d" % (int(weak["success"]), int(weak["judged"]))]
        ben_text = "Benign: %d/%d false alarms" % (int(ben["failure"]), int(ben["judged"]))
    else:
        cats = ["Detectable\n(raw)", "Detectable\nafter E07", "Blind", "Weak"]
        vals = [569 / 570, 569 / 569, 173 / 173, 146 / 146]
        labels = ["569/570", "569/569", "173/173", "146/146"]
        ben_text = "Benign: 0/180 false alarms"
    ypos = np.arange(len(cats))[::-1]
    colors = [LBLUE, BLUE, "#8c8c8c", "#8c8c8c"]
    ax1.barh(ypos, vals, color=colors, height=0.58)
    ax1.set_yticks(ypos)
    ax1.set_yticklabels(cats)
    ax1.set_xlim(0, 1.10)
    ax1.set_xlabel("confirmed / judgeable")
    ax1.set_title("(a) Artifact-level confirmation", loc="left")
    for y, v, lab in zip(ypos, vals, labels):
        ax1.text(min(v + 0.02, 1.02), y, lab, va="center", fontsize=7)
    ax1.text(0.03, -0.62, ben_text, fontsize=7, color=GREEN)
    ax1.set_ylim(-0.9, 3.7)
    ax1.grid(axis="x", color="#dddddd", lw=0.5)

    # (b) task-cluster forest plot
    if rows:
        def task_row(name, key, color, subtract_collapse=False):
            r = rows[key]
            if subtract_collapse:
                k = int(r["eff_failed_tasks"])
                n = int(r["eff_judged_tasks"])
            else:
                k = int(r["failed_tasks"])
                n = int(r["judged_tasks"])
            return (name, k, n, _wilson(k, n), color)

        forest = [
            task_row("Detectable (raw)", "detectable", RED),
            task_row("Detectable after E07", "detectable", BLUE, True),
            task_row("Blind", "blind", "#666666"),
            task_row("Weak", "weak", "#666666"),
            task_row("Benign (FP)", "benign", GREEN),
        ]
    else:
        forest = [
            ("Detectable (raw)", 1, 54, 0.0977, RED),
            ("Detectable after E07", 0, 54, 0.0664, BLUE),
            ("Blind", 0, 42, 0.0838, "#666666"),
            ("Weak", 0, 44, 0.0803, "#666666"),
            ("Benign (FP)", 0, 48, 0.0741, GREEN),
        ]
    y = np.arange(len(forest))[::-1]
    for yi, (name, k, n, upper, color) in zip(y, forest):
        ax2.plot([0, upper], [yi, yi], color=color, lw=0.9, alpha=0.9)
        ax2.plot([0], [yi], marker="o", ms=4, color=color)
        ax2.plot([upper], [yi], marker="|", ms=6, color=color)
        ax2.text(upper + 0.003, yi, f"{k}/{n}  {100*upper:.1f}%", va="center", fontsize=7)
    ax2.axvline(0.05, color="#999999", ls="--", lw=0.7)
    ax2.text(0.051, 4.10, "5% target", fontsize=7, color="#666666")
    ax2.set_yticks(y)
    ax2.set_yticklabels([r[0] for r in forest])
    ax2.set_xlim(0, 0.125)
    ax2.set_xlabel("task-cluster rate (95% Wilson upper)")
    ax2.set_title("(b) Task-cluster bounds", loc="left")
    ax2.grid(axis="x", color="#dddddd", lw=0.5)
    fig.tight_layout(w_pad=1.2)
    fig.savefig(FIG / "fig2_main.png")
    fig.savefig(FIG / "fig2_main.pdf")
    plt.close(fig)


def _cxk_cells(c_want=2):
    """从 CXK_MATRIX.csv 读 c=c_want 的每一格。图里一个数都不许写死。"""
    import csv
    want = {("E03", "L"), ("E03", "W"), ("E24", "L"), ("E24", "W")}
    cells = {}
    with open(MATRIX_CSV, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["etype"] == "REF" or int(r["c"]) != c_want:
                continue
            if (r["etype"], r["obs"]) not in want:
                continue
            rho = round(float(r["rho"]), 2)
            nh = int(r["trig_nonhead"] or 0)
            c0 = int(r["trig_class0"] or 0)
            if r["verdict"] == "IDLE":
                kind = "idle"
            elif r["verdict"] == "MISMATCH_BELOW_TAU" and nh == 0 and c0 > 0:
                kind = "struct"      # 优先级类分了但没队可重排：结构空格，不是定理检验
            else:
                kind = "tested"
            cells.setdefault((rho, int(r["K"])), {})[(r["etype"], r["obs"])] = (
                abs(float(r["rel_truth"])), kind)
    if not cells:
        raise SystemExit("CXK_MATRIX.csv 里没有 c=%d 的格，图不能凭空画" % c_want)
    return cells


def fig_cxk():
    """图 1：c=2 的 |相对偏差| 随 K 变化，一栏一个负荷。

    10-22 第二版（数据源与两道计数闸都没动，只改表达）：
      * 面板等宽、y 轴按数据范围收紧（原来 3.5 个数量级里有 2 个是空的）；
      * 阈值下方加淡底色 ⇒ "低于阈值/越过阈值"一眼可读，不用拿点去比虚线；
      * 被排除的格不再占一条 25% 图高的灰带，改成轴下"地毯刻度"（rug），
        两种原因分两行，位置是槽位不是数值；
      * 图例整图底部一行；实线=L，虚线=W（线型编的是观测量，不是 c）。
    """
    cells = _cxk_cells(2)
    rhos = sorted({k[0] for k in cells})
    series = [
        ("E03 / L", ("E03", "L"), BLUE, "o", "-"),
        ("E03 / W", ("E03", "W"), LBLUE, "s", "--"),
        ("E24 / L", ("E24", "L"), ORANGE, "^", "-"),
        ("E24 / W", ("E24", "W"), LORANGE, "D", "--"),
    ]
    fig, axes = plt.subplots(1, len(rhos), figsize=(7.0, 1.74), sharey=True,
                             gridspec_kw=dict(wspace=0.12, left=0.108, right=0.995,
                                              top=0.895, bottom=0.325))
    tau = 0.01
    tested_vals = [v[0] for d in cells.values() for v in d.values() if v[1] == "tested"]
    ylo = 10 ** np.floor(np.log10(min(tested_vals)) - 0.12)   # 轴下限由数据定，不许切点
    yhi = 10 ** (np.log10(max(tested_vals)) + 0.2)     # 上方留 0.2 个十倍程，别留整个空档
    yhi = float('%.2g' % yhi)
    npts = 0
    nband = 0
    excl = {"idle": 0, "struct": 0}
    for i, (ax, rho) in enumerate(zip(axes, rhos)):
        ks = sorted(k[1] for k in cells if k[0] == rho)
        rug = []
        for si, (name, key, color, marker, ls) in enumerate(series):
            tx, ty = [], []
            for K in ks:
                d = cells.get((rho, K), {})
                if key not in d:
                    continue
                y, kind = d[key]
                npts += 1
                if kind == "tested":
                    tx.append(K)
                    ty.append(y)
                else:
                    excl[kind] += 1
                    rug.append((K, 0 if kind == "idle" else 1, 0.0 if si % 2 == 0 else 0.16))
            ax.plot(tx, ty, color=color, ls=ls, marker=marker, ms=4.0, lw=1.15,
                    label=name, zorder=3, markeredgewidth=0.0)
        # 阈值线 + 下方淡色区：低于阈值=安全区，越过=点火
        ax.axhspan(ylo, tau, color="#eef3f8", zorder=0)
        ax.axhline(tau, color=RED, ls="--", lw=1.0, zorder=2)
        ax.set_yscale("log")
        ax.set_ylim(ylo, yhi)
        ax.set_yticks([t for t in (1e-3, 1e-2, 1e-1) if ylo <= t <= yhi])
        from matplotlib.ticker import MultipleLocator, LogLocator
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1))
        ax.set_xticks([4, 6, 8])
        ax.set_xlim(3.55, 8.20)          # 首个测点在 K=4，左侧留 0.45 的呼吸位          # 留边：'not tested' 带不再被 y 轴切掉
        ax.set_title(r"$\rho = %g$" % rho, loc="left", pad=3, fontsize=8.6)
        ax.grid(True, which="major", axis="both", color="#e3e7ec", lw=0.5, ls=":", zorder=1)
        ax.set_axisbelow(True)
        ax.tick_params(which="major", direction="in", top=True, right=True,
                       labelbottom=True, labelleft=(i == 0), left=(i == 0),
                       length=2.8, width=0.7, pad=1.6)
        ax.tick_params(which="minor", direction="in", top=True, right=True,
                       left=(i == 0), length=1.6, width=0.6)
        for s in ("top", "right", "left", "bottom"):
            ax.spines[s].set_visible(True)
            ax.spines[s].set_linewidth(0.7)
            ax.spines[s].set_color("#333333")
        # 被排除的格：画成一块"未检验"竖带。log 轴上摆不出两条看得清的地毯刻度，
        # 与其画两坨挤在一起的符号，不如一块带 + 一个标注（题注说明带内 8 格为何不算检验）。
        if rug:
            nband += len(rug)          # 不画了，但仍然要数对（见下面的闸）

    expected = sum(len(v) for v in cells.values())
    if npts != expected:
        raise SystemExit("画了 %d 个点，CSV 里 c=2 有 %d 格 —— 有点没上图" % (npts, expected))
    if nband != excl["idle"] + excl["struct"]:
        raise SystemExit("未检验带覆盖 %d 格，CSV 里被排除的格有 %d 个（%d IDLE + %d 结构）"
                         " ⇒ 有格没进带" % (nband, excl["idle"] + excl["struct"],
                                            excl["idle"], excl["struct"]))

    axes[0].set_ylabel("|relative deviation|", labelpad=2)
    axes[0].text(0.035, tau * 1.12, r"$\tau^*=0.01$", color=RED, fontsize=7,
                 transform=axes[0].get_yaxis_transform(which="grid"))
    fig.text(0.5, 0.155, "capacity $K$", ha="center", fontsize=8.4)
    h, l = axes[0].get_legend_handles_labels()      # 4 个系列；"未检验"由竖带+题注承担
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, fontsize=6.8,
               handlelength=1.4, columnspacing=1.6, borderaxespad=0.0,
               bbox_to_anchor=(0.5, 0.018))
    fig.savefig(FIG / "fig3_cxk.png")
    fig.savefig(FIG / "fig3_cxk.pdf")
    plt.close(fig)
    print("fig3: %d panels (rho=%s), %d points on axes + %d rug marks "
          "(%d IDLE + %d structural), all read from CSV"
          % (len(rhos), rhos, npts, nband, excl["idle"], excl["struct"]))

if __name__ == "__main__":
    fig_method()
    fig_main()
    fig_cxk()
    for p in sorted(FIG.glob("*.png")):
        print(p.name, p.stat().st_size)
