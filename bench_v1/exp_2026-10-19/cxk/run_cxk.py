#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the c x K mmcK sweep: REF + E03 + E24, R=10, horizon=40000.

Cells are read with criteria.j1_analytic at tau*=0.01. A cell is:
  TP                  judge fired (rel > tau)
  MISMATCH_BELOW_TAU  mechanism ran (trigger counter > 0) but rel <= tau
  IDLE                mechanism did not run (trigger counter == 0)
  NO_DATA / CRASH     field missing / subprocess failed
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent
sys.path.insert(0, str(BENCH))

import criteria as C  # noqa: E402

TASKS = HERE / "tasks_cxk.jsonl"
ART = HERE / "artifacts"
OUT_CSV = HERE / "CXK_MATRIX.csv"
OUT_MD = HERE / "CXK_SUMMARY.md"
SEEDS = 10
HOR = 40000.0
TAU = 0.01
FIELDS = ("L", "W")
ETYPES = ("REF", "E03", "E24")


def as_int(x):
    try:
        return int(x)
    except Exception:
        return None


def main() -> None:
    tasks = [json.loads(line) for line in TASKS.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_id = {t["task_id"]: t for t in tasks}
    rows = []
    ref_obs = {}
    ref_warn = []

    for task in tasks:
        tid = task["task_id"]
        c, k = task["params"]["c"], task["params"]["K"]
        lam, mu = task["params"]["lambda"], task["params"]["mu"]
        rho = lam / (c * mu)
        for etype in ETYPES:
            path = ART / f"{tid}__{etype}.py"
            obs, wall, note = C.run_artifact(path, SEEDS, HOR, "none", 1, timeout=420)
            if obs is None:
                for o in FIELDS:
                    rows.append(dict(
                        task_id=tid, c=c, K=k, lam=lam, mu=mu, rho=round(rho, 6),
                        etype=etype, obs=o, est=None, truth=None, rel_truth=None,
                        rel_ref=None, **{"fired_0.01": None}, status="run_failed",
                        trig_nonhead=None, trig_class0=None, verdict="CRASH",
                        wall=round(wall, 3), note=(note or "")[:200],
                    ))
                continue
            j = C.j1_analytic(obs, task, tau=TAU)
            if etype == "REF":
                ref_obs[tid] = obs
            for o in FIELDS:
                d = j["per_obs"].get(o, {})
                rel = d.get("rel")
                status = d.get("status", "missing")
                fired = d.get("fired")
                est = d.get("est")
                truth = d.get("truth")
                tn = as_int(obs.get("trig_nonhead"))
                tc = as_int(obs.get("trig_class0"))
                rel_ref = None
                if etype != "REF" and tid in ref_obs:
                    r = ref_obs[tid].get(o)
                    if r is not None and est is not None and abs(r) > 1e-12:
                        rel_ref = (est - r) / abs(r)
                if etype == "REF":
                    verdict = "REF"
                    if rel is not None and abs(rel) > 0.05:
                        ref_warn.append((tid, o, rel))
                elif status != "ok" or rel is None:
                    verdict = "NO_DATA"
                elif fired:
                    verdict = "TP"
                else:
                    if etype == "E03":
                        active = (tn is not None and tn > 0)
                    else:
                        active = ((tc is not None and tc > 0) or (tn is not None and tn > 0))
                    if tn is None and tc is None:
                        verdict = "NO_TRIG_FIELD"
                    elif active:
                        verdict = "MISMATCH_BELOW_TAU"
                    else:
                        verdict = "IDLE"
                rows.append(dict(
                    task_id=tid, c=c, K=k, lam=lam, mu=mu, rho=round(rho, 6),
                    etype=etype, obs=o, est=est, truth=truth,
                    rel_truth=rel, rel_ref=rel_ref,
                    **{"fired_0.01": (None if fired is None else int(bool(fired)))},
                    status=status, trig_nonhead=tn, trig_class0=tc,
                    verdict=verdict, wall=round(wall, 3), note=(note or "")[:200],
                ))

    fields = [
        "task_id", "c", "K", "lam", "mu", "rho", "etype", "obs", "est", "truth",
        "rel_truth", "rel_ref", "fired_0.01", "status", "trig_nonhead",
        "trig_class0", "verdict", "wall", "note",
    ]
    tmp = str(OUT_CSV) + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    os.replace(tmp, OUT_CSV)   # 半份矩阵比没有矩阵更坏：它看起来像证据

    # summary keyed by task and cell
    by_task = defaultdict(dict)
    for r in rows:
        if r["etype"] == "REF":
            continue
        by_task[r["task_id"]][f"{r['etype']}/{r['obs']}"] = r
    counts = Counter(r["verdict"] for r in rows if r["etype"] != "REF")
    ref_rows = [r for r in rows if r["etype"] == "REF"]
    ref_abs = [abs(r["rel_truth"]) for r in ref_rows if r["rel_truth"] is not None]

    lines = []
    lines.append("# c×K 扫描：mmcK 的 E03/E24（R=10, horizon=40000, τ*=0.01）\n")
    lines.append(f"- 题数：{len(tasks)}；件数：{len(tasks) * 3}；运行记录：{len(rows)} 个 task×etype×obs。")
    lines.append(f"- 判定：TP / MISMATCH_BELOW_TAU / IDLE / NO_DATA / CRASH。")
    lines.append(f"- 触发计数：E03 看 `trig_nonhead`；E24 看 `trig_class0` 或 `trig_nonhead`。\n")
    lines.append("## 1. REF 真值 sanity\n")
    if ref_abs:
        lines.append(f"- REF 的 |rel vs truth| 最大：{max(ref_abs):.4f}；超过 5% 的格：{len(ref_warn)}。")
        if ref_warn:
            for tid, o, rel in ref_warn[:20]:
                lines.append(f"  - {tid} {o}: rel={rel:.4f}")
    else:
        lines.append("- 无 REF 可判格。")
    lines.append("")

    lines.append("## 2. 逐题四格\n")
    header = ["task", "c", "K", "rho", "E03/L", "E03/W", "E24/L", "E24/W"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for task in tasks:
        tid = task["task_id"]
        c, k = task["params"]["c"], task["params"]["K"]
        rho = task["params"]["lambda"] / (c * task["params"]["mu"])
        cells = []
        for key in ("E03/L", "E03/W", "E24/L", "E24/W"):
            r = by_task[tid].get(key)
            if not r:
                cells.append("—")
                continue
            rel = "—" if r["rel_truth"] is None else f"{r['rel_truth']:+.5f}"
            trig = r["trig_nonhead"] if r["etype"] == "E03" else r["trig_class0"]
            cells.append(f"{r['verdict']} rel={rel} trig={trig}")
        lines.append(f"| {tid} | {c} | {k} | {rho:.2f} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## 3. 判定计数\n")
    for k, v in sorted(counts.items()):
        lines.append(f"- {k}: {v}")
    lines.append("")

    lines.append("## 4. 边界\n")
    # For each c, smallest K with any TP / any MISMATCH / any active trigger.
    for c in sorted({t["params"]["c"] for t in tasks}):
        sub = [r for r in rows if r["etype"] != "REF" and r["c"] == c]
        ks = sorted({r["K"] for r in sub})
        def first_k(pred):
            for k in ks:
                if any(pred(r) for r in sub if r["K"] == k):
                    return k
            return None
        first_tp = first_k(lambda r: r["verdict"] == "TP")
        first_mis = first_k(lambda r: r["verdict"] == "MISMATCH_BELOW_TAU")
        first_active = first_k(lambda r: (r["trig_nonhead"] or 0) > 0 or (r["trig_class0"] or 0) > 0)
        lines.append(f"- c={c}: 首次 TP K={first_tp}; 首次 MISMATCH K={first_mis}; 首次有触发 K={first_active}")
    lines.append("")

    lines.append("## 5. c=2,K=4 控制（应与 2→6 的 8 格一致）\n")
    control = [r for r in rows if r["etype"] != "REF" and r["c"] == 2 and r["K"] == 4]
    ctrl_mis = [r for r in control if r["verdict"] == "MISMATCH_BELOW_TAU"]
    ctrl_tp = [r for r in control if r["verdict"] == "TP"]
    nrho = len({r["rho"] for r in control})
    lines.append(f"- c=2,K=4 共 {len(control)} 个格（现算 {nrho} 个 ρ × 2 错型 × 2 观测量；"
                 f"ρ={sorted({r['rho'] for r in control})}）。")
    lines.append(f"- MISMATCH {len(ctrl_mis)} 个；TP {len(ctrl_tp)} 个。")
    for r in control:
        lines.append(
            f"  - {r['task_id']} {r['etype']}/{r['obs']}: rel={r['rel_truth']} "
            f"trig_nonhead={r['trig_nonhead']} trig_class0={r['trig_class0']} → {r['verdict']}"
        )
    lines.append("")

    lines.append("## 6. 读法\n")
    lines.append("- 若 K 增大后 `MISMATCH_BELOW_TAU` 变成 `TP`，8 格是**功效/阈值边界**，不是定理假。")
    lines.append("- 若 K 增大到 8 仍 `MISMATCH_BELOW_TAU`，说明该参数域内 L/W 的效应稳定低于 τ*=0.01；")
    lines.append("  定理只能主张“原则上可检”，判据侧的 operational power 需要另写边界。")
    lines.append("- `IDLE` 是机制没跑（例如 K=c 或只有一个等待位），不是定理反例；不能算进 MISMATCH。")
    lines.append("")

    _tmp = str(OUT_MD) + ".tmp"
    with open(_tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    os.replace(_tmp, OUT_MD)
    print(f"wrote {OUT_CSV}")
    print(f"wrote {OUT_MD}")
    print("counts", dict(counts))
    print("ref_max_abs_rel", max(ref_abs) if ref_abs else None, "ref_warn", len(ref_warn))
    print("control_mismatch", len(ctrl_mis), "control_tp", len(ctrl_tp))


if __name__ == "__main__":
    main()
