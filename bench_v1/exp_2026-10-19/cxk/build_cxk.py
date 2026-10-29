#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the c x K grid for mmcK and the thin artifacts.

The authoritative tasks.jsonl is read-only here. New tasks live in
tasks_cxk.jsonl; artifacts import simcore_cxk, which preloads that file into
simcore._CACHE['tb'].
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

import bench  # noqa: E402

TASKS = HERE / "tasks_cxk.jsonl"
ART = HERE / "artifacts"
GRID_CSV = HERE / "CXK_GRID.csv"

# (c, K, lambda, mu). K >= c is required; rho = lambda/(c*mu).
GRID = [
    (2, 2, 8, 5),    # no waiting slot: boundary control
    (2, 3, 8, 5),    # one waiting slot
    (2, 4, 6, 10),   # rho=0.3 control (same cell as mmcK-02)
    (2, 4, 6, 5),    # rho=0.6 control (same cell as mmcK-01)
    (2, 4, 8, 5),    # rho=0.8 control (same cell as mmcK-03)
    (2, 4, 8, 10),   # rho=0.4 control (same cell as mmcK-04), added 2026-10-20
    (2, 6, 8, 10),   # rho=0.4, K=6
    (2, 8, 8, 10),   # rho=0.4, K=8
    (2, 6, 8, 5),
    (2, 8, 8, 5),
    (2, 8, 6, 10),   # rho=0.3, large K
    (3, 3, 12, 5),   # no waiting slot
    (3, 4, 12, 5),   # one waiting slot
    (3, 6, 12, 5),
    (3, 8, 12, 5),
    (3, 8, 9, 10),   # rho=0.3, large K
    (4, 4, 16, 5),   # no waiting slot
    (4, 6, 16, 5),
    (4, 8, 16, 5),
    (4, 8, 12, 10),  # rho=0.3, large K
]


def task_id(c: int, k: int, rho: float) -> str:
    return f"cxk-mmcK-c{c}-K{k}-rho{int(round(rho * 100)):02d}"


def artifact_text(tid: str, etype: str) -> str:
    return f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""c x K sweep artifact: {tid} / {etype}."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore_cxk

simcore_cxk.simcore.main('{tid}', '{etype}')
'''


def main() -> None:
    ART.mkdir(parents=True, exist_ok=True)
    tasks = []
    rows = []
    for c, k, lam, mu in GRID:
        if k < c:
            raise SystemExit(f"invalid grid: c={c} K={k} (K < c)")
        rho = lam / (c * mu)
        if rho >= 0.98:
            raise SystemExit(f"invalid grid: c={c} K={k} lambda={lam} mu={mu} rho={rho}")
        t = bench.mmcK_truth(lam, mu, c, k)
        pf = bench.mmcK_productform(lam, mu, c, k)
        for key in ("L", "p_loss", "W", "busy_frac"):
            a, b = t[key], pf[key]
            if b is None or abs(a - b) > 1e-8 * max(1.0, abs(b)):
                raise SystemExit(
                    f"truth mismatch {c}/{k}/{lam}/{mu} {key}: {a!r} vs {b!r}"
                )
        p = dict(c=c, K=k, **{"lambda": lam}, mu=mu, service_min=round(60.0 / mu, 4))
        tid = task_id(c, k, rho)
        contract = bench._contract("queue", "mmcK")
        contract["busy_frac"] = bench.BUSY_TEXT["occupied"]
        task = dict(
            task_id=tid,
            template="mmcK",
            kind="queue",
            params=p,
            busy_def="occupied",
            truth_raw=t,
            truth_print=bench._unit_fields("queue", "mmcK", t),
            output_contract=contract,
            simpy_ref=bench.simpy_ref("mmcK", p),
            desc_zh=bench.DESC["mmcK"]["zh"].format(**p),
            desc_en=bench.DESC["mmcK"]["en"].format(**p),
        )
        tasks.append(task)
        rows.append(
            dict(
                task_id=tid,
                c=c,
                K=k,
                lam=lam,
                mu=mu,
                rho=round(rho, 6),
                service_min=p["service_min"],
                truth_L=t["L"],
                truth_W_min=t["W"] * 60.0,
                truth_p_loss=t["p_loss"],
                truth_busy_frac=t["busy_frac"],
            )
        )

    tids = [t["task_id"] for t in tasks]
    if len(set(tids)) != len(tids):
        raise SystemExit("duplicate task_id in grid")
    with open(TASKS, "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    with open(GRID_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    for t in tasks:
        tid = t["task_id"]
        for etype in ("REF", "E03", "E24"):
            fn = ART / f"{tid}__{etype}.py"
            fn.write_text(artifact_text(tid, etype), encoding="utf-8")

    print(f"tasks={len(tasks)} artifacts={len(tasks) * 3}")
    print(f"wrote {TASKS}")
    print(f"wrote {GRID_CSV}")
    print(f"wrote {ART}")


if __name__ == "__main__":
    main()
