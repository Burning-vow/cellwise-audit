#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-run mmc-05/E07 and two positive controls (mmc-06/E07, mmc-02/E07).

Purpose: distinguish a judge failure from a definition collapse.
mmc-05 has lambda == mu, so E07 (lambda<->mu swap) is a no-op.
mmc-02/06 have lambda != mu, so E07 must change the observable system.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent
sys.path.insert(0, str(BENCH))

import criteria as C  # noqa: E402

OUT_CSV = HERE / "E07_RECHECK.csv"
OUT_MD = HERE / "E07_RECHECK.md"
SEEDS = 10
HOR = 40000.0
TAU = 0.01
TASK_IDS = ("mmc-05", "mmc-06", "mmc-02")
FIELDS = ("L", "W", "p_loss", "busy_frac")


def main() -> None:
    by_id = {t["task_id"]: t for t in C.load_tasks()}
    rows = []
    for tid in TASK_IDS:
        task = by_id[tid]
        ref_path = BENCH / "artifacts" / f"{tid}__REF.py"
        mut_path = BENCH / "artifacts" / f"{tid}__e07.py"
        ref_obs, ref_wall, ref_note = C.run_artifact(ref_path, SEEDS, HOR, "none", 1, timeout=420)
        mut_obs, mut_wall, mut_note = C.run_artifact(mut_path, SEEDS, HOR, "none", 1, timeout=420)
        params = task["params"]
        if ref_obs is None or mut_obs is None:
            rows.append(dict(
                task_id=tid, c=params.get("c"), lam=params.get("lambda"), mu=params.get("mu"),
                field="ALL", ref=None, mut=None, abs_diff=None, rel_diff=None,
                rel_truth=None, **{"fired_0.01": None}, status="run_failed",
                ref_note=(ref_note or "")[:200], mut_note=(mut_note or "")[:200],
            ))
            continue
        j = C.j1_analytic(mut_obs, task, tau=TAU)
        for field in FIELDS:
            ref = ref_obs.get(field)
            mut = mut_obs.get(field)
            abs_diff = None if ref is None or mut is None else mut - ref
            rel_diff = None
            if ref is not None and mut is not None and abs(ref) > 1e-12:
                rel_diff = (mut - ref) / abs(ref)
            d = j["per_obs"].get(field, {})
            rows.append(dict(
                task_id=tid, c=params.get("c"), lam=params.get("lambda"), mu=params.get("mu"),
                field=field, ref=ref, mut=mut, abs_diff=abs_diff, rel_diff=rel_diff,
                rel_truth=d.get("rel"),
                **{"fired_0.01": (None if d.get("fired") is None else int(bool(d.get("fired"))))},
                status=d.get("status", "missing"),
                ref_note=(ref_note or "")[:200], mut_note=(mut_note or "")[:200],
            ))
        # A strict bit-identity check over the contract fields.
        same = all(
            ref_obs.get(f) == mut_obs.get(f)
            for f in FIELDS
            if ref_obs.get(f) is not None or mut_obs.get(f) is not None
        )
        rows.append(dict(
            task_id=tid, c=params.get("c"), lam=params.get("lambda"), mu=params.get("mu"),
            field="BIT_IDENTICAL", ref=None, mut=None, abs_diff=None, rel_diff=None,
            rel_truth=None, **{"fired_0.01": None}, status="identical" if same else "different",
            ref_note=(ref_note or "")[:200], mut_note=(mut_note or "")[:200],
        ))

    fields = ["task_id", "c", "lam", "mu", "field", "ref", "mut", "abs_diff",
              "rel_diff", "rel_truth", "fired_0.01", "status", "ref_note", "mut_note"]
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    lines = []
    lines.append("# E07 复跑：mmc-05（λ=μ）与正对照（λ≠μ）\n")
    lines.append(f"- 预算：R={SEEDS}，horizon={HOR:g}，seed_start=1，pert=none；判据 τ*=0.01。")
    lines.append("- E07 hook：`rate_units='lam_mu_swap'`，把 λ 与 μ 互换。\n")
    for tid in TASK_IDS:
        sub = [r for r in rows if r["task_id"] == tid]
        if not sub:
            continue
        p = by_id[tid]["params"]
        lines.append(f"## {tid}（c={p.get('c')}, λ={p.get('lambda')}, μ={p.get('mu')}）\n")
        lines.append("| 字段 | REF | E07 | 绝对差 | 相对差 | rel vs truth | fired 0.01 |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for r in sub:
            if r["field"] == "BIT_IDENTICAL":
                continue
            def fmt(x):
                return "—" if x is None else f"{x:.6g}"

            def fmt_signed(x):
                return "—" if x is None else f"{x:+.6g}"

            lines.append(
                f"| {r['field']} | {fmt(r['ref'])} | {fmt(r['mut'])} | {fmt(r['abs_diff'])} | "
                f"{fmt_signed(r['rel_diff'])} | {fmt_signed(r['rel_truth'])} | "
                f"{('—' if r['fired_0.01'] is None else r['fired_0.01'])} |"
            )
        bit = [r for r in sub if r["field"] == "BIT_IDENTICAL"]
        if bit:
            lines.append(f"\n- 契约字段逐位比较：**{bit[0]['status']}**。")
        lines.append("")

    lines.append("## 读法\n")
    lines.append("- `mmc-05`：λ=μ=10，交换 λ/μ 是 no-op；若逐位相同且 fired=0，则 569/570 的 1 件 MISS 是**定义塌缩**，不是判据失败。")
    lines.append("- `mmc-06` / `mmc-02`：λ≠μ，交换会改变系统；若字段有差且 fired=1，说明 E07 本身可检。")
    lines.append("- 结论只能是二者之一：E07 错型有效 + mmc-05 退化；或 E07 错型在非退化题上也不响应。")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")
    for r in rows:
        if r["field"] == "BIT_IDENTICAL":
            print(r["task_id"], r["status"])
        elif r["fired_0.01"] is not None:
            print(r["task_id"], r["field"], "rel_ref=", r["rel_diff"], "fired=", r["fired_0.01"])


if __name__ == "__main__":
    main()
