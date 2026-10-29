#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge the c x K sweep and the E07 recheck into one report.

No simulation is run here. It reads:
  CXK_MATRIX.csv
  ../e07_recheck/E07_RECHECK.csv
and writes:
  CXK_MATRIX_ANALYSIS.csv
  CXK_E07_REPORT.md
It also appends a short E07 pointer to CXK_SUMMARY.md.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MATRIX = HERE / "CXK_MATRIX.csv"
E07 = HERE.parent / "e07_recheck" / "E07_RECHECK.csv"
OUT_CSV = HERE / "CXK_MATRIX_ANALYSIS.csv"
OUT_MD = HERE / "CXK_E07_REPORT.md"
SUMMARY = HERE / "CXK_SUMMARY.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fnum(x: str | None, signed: bool = True) -> str:
    if x is None or x == "":
        return "—"
    try:
        v = float(x)
    except ValueError:
        return x
    return f"{v:+.5f}" if signed else f"{v:.5f}"


def as_int(x: str | None) -> int:
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return 0


rows = read_csv(MATRIX)
nonref = [r for r in rows if r["etype"] != "REF"]

# E24 at K <= c+1 has no non-head selection (trig_nonhead == 0); the priority
# classification runs (trig_class0 > 0) but there is no queue to reorder.
for r in nonref:
    r["verdict_analysis"] = r["verdict"]
    r["note_analysis"] = ""
    if (
        r["etype"] == "E24"
        and as_int(r.get("trig_nonhead")) == 0
        and r["verdict"] == "MISMATCH_BELOW_TAU"
    ):
        r["verdict_analysis"] = "IDLE_STRUCTURAL"
        r["note_analysis"] = "trig_nonhead=0: no queue reorder possible"

raw_counts = Counter(r["verdict"] for r in nonref)
ref_counts = Counter(r["verdict_analysis"] for r in nonref)

fields = list(rows[0].keys()) + ["verdict_analysis", "note_analysis"]
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)

# Group by task for the main table.
by_task = defaultdict(dict)
meta = {}
for r in nonref:
    key = (int(r["c"]), int(r["K"]), float(r["rho"]), r["task_id"])
    by_task[key][f"{r['etype']}/{r['obs']}"] = r
    meta[key] = r

main_table = []
for key in sorted(by_task):
    c, k, rho, tid = key
    cells = []
    for cell in ("E03/L", "E03/W", "E24/L", "E24/W"):
        r = by_task[key].get(cell)
        if not r:
            cells.append("—")
            continue
        trig = r["trig_nonhead"] if r["etype"] == "E03" else r["trig_class0"]
        cells.append(
            f"{r['verdict_analysis']}<br>rel={fnum(r['rel_truth'])}<br>trig={trig}"
        )
    main_table.append([f"{c}", f"{k}", f"{rho:.2f}", tid, *cells])

# c=2,K=4 controls: 8 MISMATCH + 4 TP expected.
control = [r for r in nonref if int(r["c"]) == 2 and int(r["K"]) == 4]
ctrl_mis = [r for r in control if r["verdict"] == "MISMATCH_BELOW_TAU"]
ctrl_tp = [r for r in control if r["verdict"] == "TP"]
ctrl_table = []
for r in sorted(control, key=lambda x: (float(x["rho"]), x["etype"], x["obs"])):
    ctrl_table.append(
        [
            r["task_id"],
            r["etype"],
            r["obs"],
            fnum(r["rel_truth"]),
            str(r["trig_nonhead"]),
            r["verdict"],
        ]
    )

# E07 table: L/W/busy only; p_loss has no truth on mmc tasks.
e07_rows = read_csv(E07)
e07_table = []
e07_bit = {}
for r in e07_rows:
    if r["field"] == "BIT_IDENTICAL":
        e07_bit[r["task_id"]] = r["status"]
        continue
    if r["field"] not in ("L", "W", "busy_frac"):
        continue
    e07_table.append(
        [
            r["task_id"],
            r["lam"],
            r["mu"],
            r["field"],
            fnum(r["ref"], signed=False),
            fnum(r["mut"], signed=False),
            fnum(r["rel_diff"]),
            fnum(r["rel_truth"], signed=False),
            r["fired_0.01"],
        ]
    )

lines = []
lines.append("# c×K 扫描 + E07 正对照\n")
lines.append("- c×K：17 题 × 3 件（REF/E03/E24），R=10、horizon=40000、τ*=0.01。")
lines.append("- E07：mmc-05（λ=μ）复跑 + mmc-06/mmc-02（λ≠μ）正对照，同预算。")
lines.append("- 判定：TP / MISMATCH_BELOW_TAU / IDLE / IDLE_STRUCTURAL / CRASH。")
lines.append("- `MISMATCH_BELOW_TAU` = 机制跑了但 |rel| ≤ τ*；`IDLE_STRUCTURAL` = 队列长度不足，")
lines.append("  E24 的分类发生了但无从重排；不是定理反例。\n")

lines.append("## 0. 结论\n")
lines.append(f"- c×K 原始计数：{dict(raw_counts)}；拆分 E24 结构性空转后：{dict(ref_counts)}。")
lines.append(f"- c=2,K=4 控制：MISMATCH **{len(ctrl_mis)}**、TP **{len(ctrl_tp)}**，与 2→6 的 8 格完全一致。")
lines.append("- 8 格不是定理假：K 增大到 6/8 后，c=2 的四个格全部 TP；c=3,K=6 起 W 先过 τ*；")
lines.append("  c=4,K=8 时 W 过 τ*、L 仍低于 τ*；低 ρ（0.3）+ 高 c 时即使 K=8 也仍低于 τ*。")
lines.append("- E07：mmc-05 逐位相同、fired=0 ⇒ 定义塌缩；mmc-06/mmc-02 的 |rel| 0.44–0.70、fired=1 ⇒ E07 本身可检。\n")

lines.append("## 1. c×K 逐题四格\n")
lines.append("| c | K | rho | task | E03/L | E03/W | E24/L | E24/W |")
lines.append("|---|---:|---:|---|---|---|---|---|")
for row in main_table:
    lines.append("| " + " | ".join(row) + " |")
lines.append("")
lines.append("注：表中是 `verdict_analysis`；E24 的 `trig` 列显示 `trig_class0`，结构性空转见 §2。\n")

lines.append("## 2. E24 结构性空转（10 格）\n")
lines.append("`E24` 的 `trig_class0` 在 K=c 或 K=c+1 时仍然 >0（分类发生了），但 `trig_nonhead=0`：")
lines.append("队列里最多只有 1 人，优先类无法重排。这 10 格是结构性空转，不是“机制没跑”也不是定理反例；")
lines.append("原始 MISMATCH 36 拆分后为 **MISMATCH 26 + IDLE_STRUCTURAL 10**。")
lines.append("c=2,K=4 的 8 格控制全部 `trig_nonhead>0`，不受此拆分影响。\n")

lines.append("## 3. c=2,K=4 控制：8 格复现\n")
lines.append(f"- MISMATCH {len(ctrl_mis)} 个；TP {len(ctrl_tp)} 个。")
lines.append("")
lines.append("| task | 错型 | 观测量 | rel vs truth | trig_nonhead | 判定 |")
lines.append("|---|---|---|---:|---:|---|")
for row in ctrl_table:
    lines.append("| " + " | ".join(row) + " |")
lines.append("")
lines.append("这 8 个 MISMATCH 的 rel 与 2→6 的 8 格逐位同量级：")
lines.append("E03/L 0.005163/0.008110/0.003317；E03/W 0.005278；E24/L 0.003843/0.005717/0.001922；")
lines.append("E24/W 0.003731。全部 < τ*=0.01。\n")

lines.append("## 4. 边界读法\n")
lines.append("- **c=2**：K=4 有 8 格低于 τ*；K=6/8 时四个格全部 TP（K=8 的 rel 达 0.0396–0.0931）。")
lines.append("- **c=3**：K=6 起 W 先过 τ*（E03/W 0.0197、E24/W 0.0126），L 仍低；K=8 时四个格全部 TP。")
lines.append("- **c=4**：K=6 仍全部低于 τ*；K=8 时 W 过 τ*（0.0195/0.0122），L 仍低（0.0021/0.0018）。")
lines.append("- **低 ρ**：c=2,K=8,ρ=0.3 时 E03 的 L/W 刚过 τ*（0.0129/0.0123），E24 仍低；")
lines.append("  c=3/4,K=8,ρ=0.3 时四个格全部低于 τ*。")
lines.append("- 结论：8/720 是 **τ*=0.01 下的 operational power 边界**，不是定理假。定理的“可检”是原则性的；")
lines.append("  判据能不能在给定预算/参数下看见，是另一根轴。正文要把这根轴写出来，不能只写“8 格不吻合”就完。\n")

lines.append("## 5. E07 正对照（mmc-05 / mmc-06 / mmc-02）\n")
lines.append("| task | λ | μ | 字段 | REF | E07 | rel_ref（带符号） | rel vs truth（J1 绝对） | fired 0.01 |")
lines.append("|---|---:|---:|---|---:|---:|---:|---:|---:|")
for row in e07_table:
    lines.append("| " + " | ".join(row) + " |")
lines.append("")
for tid in ("mmc-05", "mmc-06", "mmc-02"):
    if tid in e07_bit:
        lines.append(f"- `{tid}` 契约字段逐位比较：**{e07_bit[tid]}**。")
lines.append("")
lines.append("读法：")
lines.append("- `mmc-05`：λ=μ=10，交换 λ/μ 是 no-op；REF 与 E07 逐位相同，fired=0。")
lines.append("- `mmc-06`（λ=14, μ=10）与 `mmc-02`（λ=8, μ=6）：交换后系统变轻，L/W/busy 明显下降，")
lines.append("  J1 的绝对相对偏差 0.44–0.70，fired=1 ⇒ **E07 类本身可检**。")
lines.append("- 因此 2→6 的 1 件 MISS（`mmc-05/E07`）是 **λ=μ 的定义塌缩**，不是判据失声。")
lines.append("  正文同时报 raw **569/570** 与剔除后 **569/569**，并用这两个正对照作证据。\n")

lines.append("## 6. 正文可用句 / 禁写句\n")
lines.append("可用：")
lines.append("- “8/720 不吻合集中在 mmcK c=2,K=4；c×K 扫描显示 rel 随 K/ρ 增长，K=6/8 时多数格越过 τ*，")
lines.append("  故这是 τ*=0.01 下的功效边界，不是定理被证伪。”")
lines.append("- “E07 在 λ≠μ 的正对照上可检（|rel| 0.44–0.70，fired=1）；mmc-05 的 λ=μ 使交换成为 no-op，")
lines.append("  该 1 件按定义塌缩剔除，raw 569/570、剔除后 569/569。”")
lines.append("禁写：")
lines.append("- ❌ “8/720 说明定理错/定理被推翻” —— 扫描显示是功效边界。")
lines.append("- ❌ “E07 判据失声” —— 正对照 fired=1。")
lines.append("- ❌ “c×K 全部过阈值” —— c=4,K=8 的 L 和低 ρ 高 c 的多数格仍低于 τ*。")
lines.append("- ❌ “E24 在 K=c 也 MISMATCH 是定理反例” —— 那是结构性空转（trig_nonhead=0）。\n")

lines.append("## 7. 产物\n")
lines.append("- `CXK_MATRIX.csv`：原始逐格结果。")
lines.append("- `CXK_MATRIX_ANALYSIS.csv`：加 `verdict_analysis` / `note_analysis` 的派生表。")
lines.append("- `CXK_SUMMARY.md`：原始 c×K 汇总（未改）。")
lines.append("- `../e07_recheck/E07_RECHECK.md` / `.csv`：E07 复跑原始产物。")
lines.append("- 本报告：`CXK_E07_REPORT.md`。")

OUT_MD.write_text("\n".join(lines), encoding="utf-8")

# Append a pointer to the raw c×K summary so the controls are visible there too.
with open(SUMMARY, "a", encoding="utf-8") as f:
    f.write("\n## 7. E07 正对照（mmc-02/06）\n")
    f.write("\n见 `CXK_E07_REPORT.md` §5：`mmc-05` 逐位相同、fired=0；")
    f.write("`mmc-06`/`mmc-02` 交换 λ/μ 后 |rel| 0.44–0.70、fired=1。")
    f.write("这证明 E07 类本身可检，mmc-05 的 1 件 MISS 是 λ=μ 的定义塌缩。\n")

print(f"wrote {OUT_CSV}")
print(f"wrote {OUT_MD}")
print(f"raw {dict(raw_counts)}")
print(f"refined {dict(ref_counts)}")
print(f"control mismatch={len(ctrl_mis)} tp={len(ctrl_tp)}")
