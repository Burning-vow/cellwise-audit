#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2->6 statistics package: cluster bounds, per-cell n/CI, R10c comparison,
E07 definition-collapse handling, theorem mismatch audit.

All denominators are computed from the input files with len(); the script
exits non-zero if any integrity assertion fails. It does not modify the
authoritative MUTANT_TAGS_2to6.csv.
"""
from __future__ import annotations

import csv
import glob
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent

TAGS = HERE / "MUTANT_TAGS_2to6.csv"
BEN = HERE / "BENIGN_PROOF_2to6.csv"
MUT = HERE / "mutants_2to6.jsonl"
THEOREM = HERE / "UNDETECTABILITY_MATRIX_2to6.md"
R10C = BENCH / "MUTANT_TAGS_R10c.csv"
TASKS = BENCH / "tasks.jsonl"

OUT_MD = HERE / "P3_stats_2to6.md"
OUT_CLUSTER = HERE / "P3_task_cluster_2to6.csv"
OUT_CELL = HERE / "P3_cell_n_2to6.csv"
OUT_R10C = HERE / "P3_R10c_vs_2to6.csv"
OUT_THEOREM = HERE / "P3_theorem_mismatches_2to6.csv"
OUT_ANALYSIS = HERE / "MUTANT_TAGS_2to6_analysis.csv"

CATS = ["detectable", "blind", "weak", "benign"]
OK_TAG = {
    "detectable": "TP",
    "blind": "BLIND_CONFIRM",
    "weak": "WEAK_FIRED",
    "benign": "BENIGN_OK",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / den
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{100.0 * x:.2f}%"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


# ---------------------------------------------------------------- inputs
tags = read_csv(TAGS)
ben = read_csv(BEN)
r10 = read_csv(R10C)
mutants = [json.loads(line) for line in MUT.read_text(encoding="utf-8").splitlines() if line.strip()]

if len(tags) != 1092:
    fail(f"tags rows={len(tags)}, expected 1092")
tag_keys = [(r["task_id"], r["error_type"]) for r in tags]
if len(set(tag_keys)) != len(tag_keys):
    fail("duplicate (task_id, error_type) in tags")
tag_key_set = set(tag_keys)

tasks = sorted({r["task_id"] for r in tags})
if len(tasks) != 54:
    fail(f"tasks={len(tasks)}, expected 54")
per_template = Counter(r["template"] for r in tags)
task_per_template = Counter()
for tpl in per_template:
    task_per_template[tpl] = len({r["task_id"] for r in tags if r["template"] == tpl})
if set(task_per_template.values()) != {6}:
    fail(f"task_per_template={dict(task_per_template)}, expected 6 each")

if any(r["ran"] != "1" for r in tags):
    fail("some tags rows have ran != 1")
if any(r["no_tau"] != "0" for r in tags):
    fail("some tags rows have no_tau != 0")

tag_counts = Counter(r["tag_strict_A"] for r in tags)
expected_tag_counts = {
    "TP": 569,
    "BENIGN_OK": 180,
    "BLIND_CONFIRM": 173,
    "WEAK_FIRED": 146,
    "INJECTION_IDLE": 23,
    "MISS": 1,
}
if dict(tag_counts) != expected_tag_counts:
    fail(f"tag counts={dict(tag_counts)}, expected {expected_tag_counts}")

# R10c is the pre-registered subset; all its artifact keys must be in 2->6.
r10_keys = {(r["task_id"], r["error_type"]) for r in r10}
if len(r10) != 408 or len(r10_keys) != 408:
    fail(f"R10c rows={len(r10)}, unique={len(r10_keys)}, expected 408/408")
if not r10_keys <= tag_key_set:
    fail(f"R10c has {len(r10_keys - tag_key_set)} artifact keys not in 2->6")
r10_tasks = {r["task_id"] for r in r10}
if len(r10_tasks) != 26:
    fail(f"R10c tasks={len(r10_tasks)}, expected 26")
if not r10_tasks <= set(tasks):
    fail("R10c has tasks not in 2->6")
r10_counts = Counter(r["tag_strict_A"] for r in r10)
expected_r10_counts = {
    "TP": 222,
    "BENIGN_OK": 68,
    "BLIND_CONFIRM": 57,
    "WEAK_FIRED": 50,
    "INJECTION_IDLE": 11,
}
if dict(r10_counts) != expected_r10_counts:
    fail(f"R10c tag counts={dict(r10_counts)}, expected {expected_r10_counts}")

if len(ben) != 180:
    fail(f"benign rows={len(ben)}, expected 180")
ben_keys = {(r["task_id"], r["error_type"]) for r in ben}
if len(ben_keys) != 180:
    fail(f"benign unique keys={len(ben_keys)}, expected 180")
if not ben_keys <= tag_key_set:
    fail("benign proof has artifact keys not in tags")
if any(r["verdict"] != "PROVES_BENIGN" for r in ben):
    fail("some benign rows are not PROVES_BENIGN")
ben_tasks = {r["task_id"] for r in ben}
if len(ben_tasks) != 48:
    fail(f"benign tasks={len(ben_tasks)}, expected 48")

mutant_keys = {(r["task_id"], r["error_type"]) for r in mutants}
if len(mutants) != 1092 or len(mutant_keys) != 1092:
    fail(f"mutants rows={len(mutants)}, unique={len(mutant_keys)}, expected 1092/1092")
if mutant_keys != tag_key_set:
    fail("mutant keys != tag keys")

# Matrix: include the copied 2->4 shards and the new 2->6 shards; exclude
# *.triggers.csv by using a glob that ends at the shard number.
matrix_files = sorted(
    p for p in glob.glob(str(HERE / "MUTANT_MATRIX_2to[46].shard[0-9].csv"))
)
if not matrix_files:
    fail("no matrix shard files found")
matrix_keys: set[tuple[str, str]] = set()
matrix_rows = 0
matrix_seeds: set[str] = set()
matrix_horizons: set[str] = set()
for path in matrix_files:
    rows = read_csv(Path(path))
    matrix_rows += len(rows)
    for r in rows:
        matrix_keys.add((r["task_id"], r["error_type"]))
        matrix_seeds.add(str(r["seeds"]).strip())
        matrix_horizons.add(str(r["horizon"]).strip())
if matrix_keys != tag_key_set:
    missing = sorted(tag_key_set - matrix_keys)[:5]
    extra = sorted(matrix_keys - tag_key_set)[:5]
    fail(f"matrix keys != tag keys; missing={missing} extra={extra}")
if matrix_seeds != {"10"}:
    fail(f"matrix seeds={sorted(matrix_seeds)}, expected ['10']")
if not matrix_horizons <= {"40000", "40000.0"}:
    fail(f"matrix horizons={sorted(matrix_horizons)}, expected 40000")

# E07: mmc-05 has lambda == mu, so swapping lambda/mu is a no-op.
e07 = [r for r in tags if r["task_id"] == "mmc-05" and r["error_type"] == "E07"]
if len(e07) != 1:
    fail(f"mmc-05/E07 rows={len(e07)}, expected 1")
if e07[0]["tag_strict_A"] != "MISS":
    fail("mmc-05/E07 is not tagged MISS; definition-collapse condition changed")
task_params: dict[str, dict] = {}
for line in TASKS.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    d = json.loads(line)
    task_params[d["task_id"]] = d
p5 = task_params["mmc-05"]["params"]
if p5["lambda"] != p5["mu"]:
    fail(f"mmc-05 lambda={p5['lambda']} mu={p5['mu']}; E07 is not a no-op")
lam5, mu5 = p5["lambda"], p5["mu"]

# Theorem report: parse the pre-registered total and the 8 mismatch rows.
theorem_text = THEOREM.read_text(encoding="utf-8")
m = re.search(r"总预测格\s*(\d+)，不吻合\s*(\d+)", theorem_text)
if not m:
    fail("cannot find '总预测格 ..., 不吻合 ...' in theorem report")
total_pred, total_bad = int(m.group(1)), int(m.group(2))
if (total_pred, total_bad) != (720, 8):
    fail(f"theorem total/mismatch={total_pred}/{total_bad}, expected 720/8")

mismatch_pat = re.compile(
    r"- \[P2\] (E\d+)/([LW])@(\w+)\(([^)]+)\) 预测可检 实测不点火"
    r"\(rel 最大 ([\d.]+), τ\*=([\d.]+)\)"
)
mismatches: list[dict] = []
for line in theorem_text.splitlines():
    mm = mismatch_pat.search(line)
    if mm:
        mismatches.append(
            {
                "task_id": mm.group(4),
                "error_type": mm.group(1),
                "observable": mm.group(2),
                "template": mm.group(3),
                "rel_max": float(mm.group(5)),
                "tau": float(mm.group(6)),
                "prediction": "detectable",
                "observed": "not_fired",
                "verdict": "MISMATCH",
            }
        )
if len(mismatches) != total_bad:
    fail(f"parsed {len(mismatches)} mismatch rows, expected {total_bad}")

# ------------------------------------------------------ analysis tags
analysis_rows: list[dict] = []
for r in tags:
    a = dict(r)
    if r["task_id"] == "mmc-05" and r["error_type"] == "E07":
        a["analysis_tag"] = "DEFINITION_COLLAPSE"
        a["exclude_reason"] = "lambda_eq_mu_swap_noop"
    else:
        a["analysis_tag"] = r["tag_strict_A"]
        a["exclude_reason"] = ""
    analysis_rows.append(a)

write_csv(
    OUT_ANALYSIS,
    analysis_rows,
    [
        "task_id",
        "error_type",
        "template",
        "family",
        "expected_declared",
        "tag_strict_A",
        "fired_A",
        "rows",
        "no_tau",
        "ran",
        "analysis_tag",
        "exclude_reason",
    ],
)

# ------------------------------------------------------ cluster stats
cluster_rows: list[dict] = []
cluster_by_cat: dict[str, dict] = {}

for cat in CATS:
    sub = [r for r in analysis_rows if r["expected_declared"] == cat]
    ok_tag = OK_TAG[cat]
    n = len(sub)
    idle = sum(1 for r in sub if r["tag_strict_A"] == "INJECTION_IDLE")
    miss_raw = sum(1 for r in sub if r["tag_strict_A"] == "MISS")
    collapse = sum(1 for r in sub if r["analysis_tag"] == "DEFINITION_COLLAPSE")
    ok_raw = sum(1 for r in sub if r["tag_strict_A"] == ok_tag)
    den_raw = n - idle
    den_eff = den_raw - collapse
    miss_eff = sum(1 for r in sub if r["analysis_tag"] == "MISS")
    ok_eff = sum(1 for r in sub if r["analysis_tag"] == ok_tag)

    if ok_raw + miss_raw != den_raw:
        fail(f"{cat}: raw ok+miss={ok_raw + miss_raw} != den_raw={den_raw}")
    if ok_eff + miss_eff != den_eff:
        fail(f"{cat}: eff ok+miss={ok_eff + miss_eff} != den_eff={den_eff}")
    allowed = {ok_tag, "MISS", "INJECTION_IDLE", "DEFINITION_COLLAPSE"}
    bad = sorted({r["analysis_tag"] for r in sub} - allowed)
    if bad:
        fail(f"{cat}: unexpected analysis tags {bad}")

    cat_tasks = sorted({r["task_id"] for r in sub})
    task_info: dict[str, dict] = {}
    for t in cat_tasks:
        rs = [r for r in sub if r["task_id"] == t]
        raw_judged = [r for r in rs if r["tag_strict_A"] != "INJECTION_IDLE"]
        eff_judged = [
            r
            for r in rs
            if r["analysis_tag"] not in ("INJECTION_IDLE", "DEFINITION_COLLAPSE")
        ]
        task_info[t] = {
            "raw_judged": len(raw_judged),
            "eff_judged": len(eff_judged),
            "raw_ok": bool(raw_judged) and all(r["tag_strict_A"] == ok_tag for r in raw_judged),
            "eff_ok": bool(eff_judged) and all(r["analysis_tag"] == ok_tag for r in eff_judged),
            "raw_miss": any(r["tag_strict_A"] == "MISS" for r in rs),
            "eff_miss": any(r["analysis_tag"] == "MISS" for r in rs),
        }

    tasks_total = len(cat_tasks)
    tasks_judged_raw = sum(1 for t in cat_tasks if task_info[t]["raw_judged"] > 0)
    tasks_all_ok_raw = sum(1 for t in cat_tasks if task_info[t]["raw_ok"])
    tasks_miss_raw = sum(1 for t in cat_tasks if task_info[t]["raw_miss"])
    tasks_idle_only = sum(1 for t in cat_tasks if task_info[t]["raw_judged"] == 0)
    tasks_judged_eff = sum(1 for t in cat_tasks if task_info[t]["eff_judged"] > 0)
    tasks_all_ok_eff = sum(1 for t in cat_tasks if task_info[t]["eff_ok"])
    tasks_miss_eff = sum(1 for t in cat_tasks if task_info[t]["eff_miss"])
    tasks_no_eff_judged = sum(1 for t in cat_tasks if task_info[t]["eff_judged"] == 0)

    row = {
        "category": cat,
        "tasks_total": tasks_total,
        "tasks_judged_raw": tasks_judged_raw,
        "tasks_all_ok_raw": tasks_all_ok_raw,
        "tasks_miss_raw": tasks_miss_raw,
        "tasks_idle_only": tasks_idle_only,
        "task_fail_upper_all_raw": wilson(tasks_miss_raw, tasks_total)[1],
        "task_fail_upper_judged_raw": (
            wilson(tasks_miss_raw, tasks_judged_raw)[1] if tasks_judged_raw else None
        ),
        "tasks_judged_eff": tasks_judged_eff,
        "tasks_all_ok_eff": tasks_all_ok_eff,
        "tasks_miss_eff": tasks_miss_eff,
        "tasks_no_eff_judged": tasks_no_eff_judged,
        "task_fail_upper_all_eff": wilson(tasks_miss_eff, tasks_total)[1],
        "task_fail_upper_judged_eff": (
            wilson(tasks_miss_eff, tasks_judged_eff)[1] if tasks_judged_eff else None
        ),
        "artifacts_total": n,
        "den_raw": den_raw,
        "ok_raw": ok_raw,
        "miss_raw": miss_raw,
        "idle": idle,
        "collapse": collapse,
        "den_eff": den_eff,
        "ok_eff": ok_eff,
        "miss_eff": miss_eff,
        "artifact_fail_upper_raw": wilson(miss_raw, den_raw)[1],
        "artifact_fail_upper_eff": wilson(miss_eff, den_eff)[1] if den_eff else None,
        "acc_eff": (ok_eff / den_eff) if den_eff else None,
        "acc_lower_eff": wilson(ok_eff, den_eff)[0] if den_eff else None,
    }
    cluster_rows.append(row)
    cluster_by_cat[cat] = row

# Headline assertions: catch silent drift in the 2->6 authority.
expected_cluster = {
    "detectable": (54, 54, 1, 54, 570, 569, 1, 1, 569, 569, 0),
    "blind": (42, 42, 0, 42, 173, 173, 0, 0, 173, 173, 0),
    "weak": (48, 44, 0, 44, 146, 146, 0, 0, 146, 146, 0),
    "benign": (48, 48, 0, 48, 180, 180, 0, 0, 180, 180, 0),
}
for cat, exp in expected_cluster.items():
    r = cluster_by_cat[cat]
    got = (
        r["tasks_total"],
        r["tasks_judged_raw"],
        r["tasks_miss_raw"],
        r["tasks_judged_eff"],
        r["den_raw"],
        r["ok_raw"],
        r["miss_raw"],
        r["collapse"],
        r["den_eff"],
        r["ok_eff"],
        r["miss_eff"],
    )
    if got != exp:
        fail(f"{cat}: cluster headline {got} != expected {exp}")

write_csv(
    OUT_CLUSTER,
    cluster_rows,
    [
        "category",
        "tasks_total",
        "tasks_judged_raw",
        "tasks_all_ok_raw",
        "tasks_miss_raw",
        "tasks_idle_only",
        "task_fail_upper_all_raw",
        "task_fail_upper_judged_raw",
        "tasks_judged_eff",
        "tasks_all_ok_eff",
        "tasks_miss_eff",
        "tasks_no_eff_judged",
        "task_fail_upper_all_eff",
        "task_fail_upper_judged_eff",
        "artifacts_total",
        "den_raw",
        "ok_raw",
        "miss_raw",
        "idle",
        "collapse",
        "den_eff",
        "ok_eff",
        "miss_eff",
        "artifact_fail_upper_raw",
        "artifact_fail_upper_eff",
        "acc_eff",
        "acc_lower_eff",
    ],
)

# ------------------------------------------------------ per-cell stats
cells: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
for r in analysis_rows:
    cells[(r["template"], r["family"], r["expected_declared"])].append(r)

cell_rows: list[dict] = []
for (tpl, family, cat), rs in sorted(cells.items()):
    ok_tag = OK_TAG[cat]
    n = len(rs)
    idle = sum(1 for r in rs if r["tag_strict_A"] == "INJECTION_IDLE")
    collapse = sum(1 for r in rs if r["analysis_tag"] == "DEFINITION_COLLAPSE")
    miss_raw = sum(1 for r in rs if r["tag_strict_A"] == "MISS")
    ok_raw = sum(1 for r in rs if r["tag_strict_A"] == ok_tag)
    den_raw = n - idle
    den_eff = den_raw - collapse
    miss_eff = sum(1 for r in rs if r["analysis_tag"] == "MISS")
    ok_eff = sum(1 for r in rs if r["analysis_tag"] == ok_tag)
    if ok_raw + miss_raw != den_raw:
        fail(f"{tpl}/{family}/{cat}: raw sum mismatch")
    if ok_eff + miss_eff != den_eff:
        fail(f"{tpl}/{family}/{cat}: eff sum mismatch")

    notes = []
    if idle:
        notes.append(f"IDLE={idle}")
    if collapse:
        notes.append(f"DEFINITION_COLLAPSE={collapse}")
    if miss_eff:
        notes.append(f"MISS={miss_eff}")
    if den_eff == 0:
        notes.append("no_judged")
    acc_eff = (ok_eff / den_eff) if den_eff else None
    cell_rows.append(
        {
            "template": tpl,
            "family": family,
            "category": cat,
            "n": n,
            "den_raw": den_raw,
            "ok_raw": ok_raw,
            "miss_raw": miss_raw,
            "idle": idle,
            "collapse": collapse,
            "den_eff": den_eff,
            "ok_eff": ok_eff,
            "miss_eff": miss_eff,
            "acc_eff": acc_eff,
            "acc_lower_eff": wilson(ok_eff, den_eff)[0] if den_eff else None,
            "fail_upper_eff": wilson(miss_eff, den_eff)[1] if den_eff else None,
            "under_powered": "1" if den_eff <= 6 else "0",
            "note": "; ".join(notes),
        }
    )

write_csv(
    OUT_CELL,
    cell_rows,
    [
        "template",
        "family",
        "category",
        "n",
        "den_raw",
        "ok_raw",
        "miss_raw",
        "idle",
        "collapse",
        "den_eff",
        "ok_eff",
        "miss_eff",
        "acc_eff",
        "acc_lower_eff",
        "fail_upper_eff",
        "under_powered",
        "note",
    ],
)

cells_total = len(cell_rows)
cells_small = sum(1 for r in cell_rows if r["under_powered"] == "1")
cells_no_judged = sum(1 for r in cell_rows if r["den_eff"] == 0)
cells_fail = sum(1 for r in cell_rows if r["miss_eff"] > 0)
cells_100_10 = sum(
    1 for r in cell_rows if r["den_eff"] >= 10 and r["acc_eff"] == 1.0
)
cells_100_any = sum(
    1 for r in cell_rows if r["den_eff"] > 0 and r["acc_eff"] == 1.0
)

# ------------------------------------------------------ R10c vs 2->6
r10_vs_26 = [
    ("tasks", len(r10_tasks), len(tasks), len(tasks) - len(r10_tasks)),
    ("artifacts", len(r10), len(tags), len(tags) - len(r10)),
    ("TP", r10_counts.get("TP", 0), tag_counts.get("TP", 0), tag_counts.get("TP", 0) - r10_counts.get("TP", 0)),
    ("MISS", r10_counts.get("MISS", 0), tag_counts.get("MISS", 0), tag_counts.get("MISS", 0) - r10_counts.get("MISS", 0)),
    ("BLIND_CONFIRM", r10_counts.get("BLIND_CONFIRM", 0), tag_counts.get("BLIND_CONFIRM", 0), tag_counts.get("BLIND_CONFIRM", 0) - r10_counts.get("BLIND_CONFIRM", 0)),
    ("WEAK_FIRED", r10_counts.get("WEAK_FIRED", 0), tag_counts.get("WEAK_FIRED", 0), tag_counts.get("WEAK_FIRED", 0) - r10_counts.get("WEAK_FIRED", 0)),
    ("BENIGN_OK", r10_counts.get("BENIGN_OK", 0), tag_counts.get("BENIGN_OK", 0), tag_counts.get("BENIGN_OK", 0) - r10_counts.get("BENIGN_OK", 0)),
    ("INJECTION_IDLE", r10_counts.get("INJECTION_IDLE", 0), tag_counts.get("INJECTION_IDLE", 0), tag_counts.get("INJECTION_IDLE", 0) - r10_counts.get("INJECTION_IDLE", 0)),
]
write_csv(
    OUT_R10C,
    [
        {"metric": m, "r10c_pre_registered": a, "two_to_six": b, "delta": d}
        for m, a, b, d in r10_vs_26
    ],
    ["metric", "r10c_pre_registered", "two_to_six", "delta"],
)

# ------------------------------------------------------ theorem CSV
write_csv(
    OUT_THEOREM,
    mismatches,
    [
        "task_id",
        "error_type",
        "observable",
        "template",
        "rel_max",
        "tau",
        "prediction",
        "observed",
        "verdict",
    ],
)

# ------------------------------------------------------ report
cluster_table = markdown_table(
    ["类别", "工件 raw", "工件 eff", "题簇 raw", "题簇 eff", "题簇上界 raw/eff", "备注"],
    [
        [
            cat,
            f"{r['ok_raw']}/{r['den_raw']}",
            f"{r['ok_eff']}/{r['den_eff']}",
            f"{r['tasks_all_ok_raw']}/{r['tasks_total']}",
            f"{r['tasks_all_ok_eff']}/{r['tasks_total']}",
            f"{pct(r['task_fail_upper_all_raw'])} / {pct(r['task_fail_upper_all_eff'])}",
            (
                f"IDLE={r['idle']}; collapse={r['collapse']}; "
                f"judged tasks={r['tasks_judged_raw']}; idle-only={r['tasks_idle_only']}"
            ),
        ]
        for cat, r in ((c, cluster_by_cat[c]) for c in CATS)
    ],
)

r10_table = markdown_table(
    ["指标", "R10c（预注册）", "2→6（扩展）", "差值"],
    [[m, str(a), str(b), f"{d:+d}"] for m, a, b, d in r10_vs_26],
)

theorem_groups = Counter((r["error_type"], r["observable"]) for r in mismatches)
theorem_tasks = Counter(r["task_id"] for r in mismatches)
rel_min = min(r["rel_max"] for r in mismatches)
rel_max = max(r["rel_max"] for r in mismatches)
theorem_group_text = "; ".join(
    f"{k[0]}/{k[1]}×{v}" for k, v in sorted(theorem_groups.items())
)
theorem_task_text = "; ".join(f"{k}×{v}" for k, v in sorted(theorem_tasks.items()))

d = cluster_by_cat["detectable"]
b = cluster_by_cat["blind"]
w = cluster_by_cat["weak"]
g = cluster_by_cat["benign"]

report = f"""# 2→6 统计包（54 题 / 1092 件）

- 输入：`MUTANT_TAGS_2to6.csv`（{len(tags)} 行）、`BENIGN_PROOF_2to6.csv`（{len(ben)} 行）、
  `mutants_2to6.jsonl`（{len(mutants)} 条）、`UNDETECTABILITY_MATRIX_2to6.md`。
- 对照：`MUTANT_TAGS_R10c.csv`（{len(r10)} 行，26 题，预注册子集；其 408 个工件键全部是 2→6 的子集）。
- 重跑：`PYTHONIOENCODING=utf-8 ~/miniconda3/python.exe P3_stats_2to6.py`
- 原表不改；本报告的 `analysis_tag` 是派生列，E07 的 raw/eff 两套账必须同时报。

## 0. 完整性闸

- 2→6：{len(tags)} 行，{len(tag_key_set)} 个唯一 `(task_id,error_type)`，{len(tasks)} 题，
  9 个模板各 6 题；`ran=1` 与 `no_tau=0` 全通过。
- 标签：{dict(tag_counts)}。
- 良性：{len(ben)} 行，{len(ben_tasks)} 题，全部 `PROVES_BENIGN`；工件键全部在 2→6 内。
- 矩阵：{len(matrix_files)} 个 shard（4 个 2→4 + 4 个 2→6），共 {matrix_rows} 行；工件键与 tags 全等；
  seeds={sorted(matrix_seeds)}，horizon={sorted(matrix_horizons)}。
- 定理：总预测 {total_pred} 格，不吻合 {total_bad} 格；逐行解析到 {len(mismatches)} 行。
- E07：`mmc-05/E07` 为 MISS；`mmc-05` 的 λ={lam5}、μ={mu5}，λ=μ ⇒ 交换是 no-op，
  按 `DEFINITION_COLLAPSE` 剔除，不是判据失败。

## 1. 题簇上界（主表）

{cluster_table}

读法：
- **工件级**是 1092 件里的比例；**题簇级**是“换一道同类新题”的保守上界。正文两个都要报。
- `benign 0/180 = 2.1%` 只是工件级；题簇级是 **0/{g['tasks_total']} = {pct(g['task_fail_upper_all_eff'])}**。
- `blind 173/173` 的题簇级是 **0/{b['tasks_total']} = {pct(b['task_fail_upper_all_eff'])}**；
  `weak 146/146` 的题簇级是 **0/{w['tasks_total']} = {pct(w['task_fail_upper_all_eff'])}**
  （其中 {w['tasks_idle_only']} 题只有 IDLE、没有可判弱档工件；按可判题算是 0/{w['tasks_judged_raw']} = {pct(w['task_fail_upper_judged_raw'])}）。
- `detectable` raw 是 **{d['ok_raw']}/{d['den_raw']} = {pct(d['ok_raw']/d['den_raw'])}**，
  1 件 MISS 是 E07 定义塌缩；剔除后 **{d['ok_eff']}/{d['den_eff']} = {pct(d['ok_eff']/d['den_eff'])}**。
  题簇级 raw 1/{d['tasks_total']} 上界 {pct(d['task_fail_upper_all_raw'])}；剔除后 0/{d['tasks_total']} 上界 {pct(d['task_fail_upper_all_eff'])}。

## 2. 每格 n/CI

- 共 **{cells_total}** 个 `template×family×category` 格；**{cells_small}** 格 `den_eff≤6`；
  **{cells_no_judged}** 格无判据工件；剔除 E07 后 **{cells_fail}** 格还有 MISS。
- 100% 的格共 **{cells_100_any}** 个；其中 **{cells_small}** 格 `den_eff≤6`（只能算“点着了”，不算可检），
  **{cells_100_10}** 格 `den_eff≥10`（可报 100%）；另有 **{cells_no_judged}** 格无判据工件。
- 全表见 `P3_cell_n_2to6.csv`；`under_powered=1` 的格不许写“100% 可检”。
- 典型薄格：`eoq/numerics/weak` 只有 2 个可判工件（4 个 IDLE）；`mmcK/priority/detectable`
  只有 3 个可判工件（3 个 IDLE）。这些格只能写“点着了 n 件”，不能写“该格 100%”。

## 3. R10c（预注册）→ 2→6（事后扩展）

{r10_table}

- R10c 的 26 题 / 408 件全部是 2→6 的子集，所以差值就是扩展部分：+28 题、+684 件、
  +347 TP、+1 MISS、+116 blind、+96 weak、+112 benign、+12 IDLE。
- **R10c 是预注册确证集；2→6 是事后扩展**。正文不要把 2→6 的 569/570 写成“预注册结果”。

## 4. E07 定义塌缩

- `mmc-05`：λ={lam5}、μ={mu5}；E07 交换 λ/μ，两个值相等 ⇒ 工件与参照件在观测上不可区分。
- raw：569/570 = {pct(569/570)}；剔除后：569/569 = 100.0%。
- 题簇级：raw 1/54 上界 {pct(d['task_fail_upper_all_raw'])}；剔除后 0/54 上界 {pct(d['task_fail_upper_all_eff'])}。
- 这是**定义塌缩**，不是判据失败；必须在正文写清，不许静默把 569/570 改成 569/569。

## 5. 定理 720 格对账

- 总预测 **{total_pred}** 格，不吻合 **{total_bad}** 格（{pct(total_bad/total_pred)}）。
- 8 格全部在 `mmcK-01/02/03`：{theorem_task_text}；按错型/观测量：{theorem_group_text}。
- rel 最大范围 **{rel_min:.5f}–{rel_max:.5f}**，全部低于 τ*=0.01；即“定理说可检，但判据在该参数下没点火”。
- `mmcK-01/02/03` 都是 c=2、K=4；c=3 的 `mmcK-05/06` 在这些格上是 IDLE ⇒ **c≥3 的边界还没测到**。
- 逐行见 `P3_theorem_mismatches_2to6.csv`。

## 6. 能写 / 禁写

能写：
- “2→6：可检 569/570 = 99.8%（raw）；剔除 E07 定义塌缩后 569/569 = 100%。”
- “良性 0/180 工件级（Wilson 上界 2.1%）；题簇级 0/48（上界 7.4%）。”
- “恒等类 173/173 工件级；42 题 0 误点火；题簇上界 8.4%。”
- “定理 720 格中 8 格不吻合，全部 mmcK-01/02/03，rel<τ*。”

禁写：
- ❌ “64 题全覆盖”（实际 54/64）。
- ❌ “良性 0/180 所以假阳率 ≤2.1%”（题簇级上界 7.4%）。
- ❌ “逐格 τ* 检出率更高”（2→6 里全局 0.02 仍是 569/570，规则差异 0 件）。
- ❌ “定理 100% 命中”（8/720 不吻合）。
- ❌ “人工基线/加速 N 倍”（没有独立人工基线）。
- ❌ “Qwen 50.5% > flash 29.6%” 不带 coverage（Qwen 的可比格只有 101/162=62.3%）。

## 7. 下一步（未跑）

c×K 扫描：`c∈{{2,3,4}} × K∈{{2,3,4,6,8}}`，mmcK 的 E03/E24，R=10、horizon=40000；
预注册 follow-up 预测，标明是“事后解释”，不是原来的 720 格预注册。
输出：每格 rel、τ*=0.01、fired/not，找到 rel 越过 τ* 的边界，解释 8 格是“定理错”还是“功效不够”。
"""

OUT_MD.write_text(report, encoding="utf-8")

print(f"wrote {OUT_MD}")
print(f"wrote {OUT_CLUSTER}")
print(f"wrote {OUT_CELL}")
print(f"wrote {OUT_R10C}")
print(f"wrote {OUT_THEOREM}")
print(f"wrote {OUT_ANALYSIS}")
print(
    "headline:",
    f"tags={len(tags)}",
    f"tasks={len(tasks)}",
    f"benign={g['ok_eff']}/{g['den_eff']}",
    f"benign_task_upper={pct(g['task_fail_upper_all_eff'])}",
    f"detectable_raw={d['ok_raw']}/{d['den_raw']}",
    f"detectable_eff={d['ok_eff']}/{d['den_eff']}",
    f"theorem={total_pred}/{total_bad}",
    f"cells={cells_total}",
    f"under_powered={cells_small}",
)
