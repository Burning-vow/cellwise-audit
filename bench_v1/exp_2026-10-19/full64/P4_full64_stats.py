# -*- coding: utf-8 -*-
"""Full-64 statistics package: tag counts, task-cluster bounds, per-cell n/CI,
E07 definition collapse, and theorem audit.

All denominators are computed from the input files with len(); the script exits
non-zero if the coverage assertions fail. It does not modify the authoritative
MUTANT_TAGS_full64.csv or the theorem report.
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent
TAGS = HERE / "MUTANT_TAGS_full64.csv"
BEN = HERE / "BENIGN_PROOF_full64.csv"
MUT = HERE / "mutants_all64.jsonl"
THEOREM = HERE / "UNDETECTABILITY_MATRIX_full64.md"
TASKS = BENCH / "tasks.jsonl"
MATRIX_GLOB = str(HERE / "MUTANT_MATRIX_full64.shard*.csv")

OUT_MD = HERE / "P4_full64_stats.md"
OUT_CLUSTER = HERE / "P4_task_cluster_full64.csv"
OUT_CELL = HERE / "P4_cell_n_full64.csv"
OUT_THEOREM = HERE / "P4_theorem_mismatches_full64.csv"
OUT_ANALYSIS = HERE / "MUTANT_TAGS_full64_analysis.csv"

CATS = ("detectable", "blind", "weak", "benign")
OK_TAG = {
    "detectable": "TP",
    "blind": "BLIND_CONFIRM",
    "weak": "WEAK_FIRED",
    "benign": "BENIGN_OK",
}
EXCLUDE_TAGS = {"INJECTION_IDLE", "NA_NOINST", "NA_NOTAU", "NORUN", "CRASH", "MISSING"}
COLLAPSE = "DEFINITION_COLLAPSE"


def fail(msg: str) -> None:
    print("FAIL: " + msg, file=sys.stderr)
    raise SystemExit(1)


def read_csv(path: Path) -> list[dict]:
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
    return "n/a" if x is None else "%.2f%%" % (100.0 * x)


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


# ------------------------------------------------------------------ inputs
tags = read_csv(TAGS)
ben = read_csv(BEN)
mutants = [json.loads(line) for line in MUT.read_text(encoding="utf-8").splitlines() if line.strip()]
task_rows = [json.loads(line) for line in TASKS.read_text(encoding="utf-8").splitlines() if line.strip()]
task_params = {t["task_id"]: t for t in task_rows}

if len(tags) != 1348:
    fail("tags rows=%d, expected 1348 (full64: 64 REF + 1348 mutants)" % len(tags))
tag_keys = [(r["task_id"], r["error_type"]) for r in tags]
if len(set(tag_keys)) != len(tag_keys):
    fail("duplicate (task_id, error_type) in tags")
tag_key_set = set(tag_keys)
tasks = sorted({r["task_id"] for r in tags})
if len(tasks) != 64:
    fail("tasks=%d, expected 64" % len(tasks))

norun = [r for r in tags if r["ran"] != "1"]
if any(r["ran"] not in ("1", "") for r in tags):
    fail("some tags rows have an unexpected ran value")
if any(r["no_tau"] != "0" for r in tags):
    fail("some tags rows have no_tau != 0")

tag_counts = Counter(r["tag_strict_A"] for r in tags)
expected_tag_counts = {"TP": 506, "BENIGN_OK": 196, "BLIND_CONFIRM": 191,
                       "WEAK_FIRED": 131, "INJECTION_IDLE": 21, "NA_NOINST": 303}
# Counts are checked after the missing-artifact rerun; only the total is fixed here.
if sum(tag_counts.values()) != 1348:
    fail("tag count total != 1348")

ben_keys = {(r["task_id"], r["error_type"]) for r in ben}
if len(ben) != 220 or len(ben_keys) != 220:
    fail("benign rows=%d unique=%d, expected 220/220" % (len(ben), len(ben_keys)))
if not ben_keys <= tag_key_set:
    fail("benign proof has artifact keys not in tags")
if any(r["verdict"] != "PROVES_BENIGN" for r in ben):
    fail("some benign rows are not PROVES_BENIGN")
ben_tasks = {r["task_id"] for r in ben}
if len(ben_tasks) != 58:
    fail("benign tasks=%d, expected 58" % len(ben_tasks))

mutant_keys = {(r["task_id"], r["error_type"]) for r in mutants}
if len(mutants) != 1348 or len(mutant_keys) != 1348:
    fail("mutants rows=%d unique=%d, expected 1348/1348" % (len(mutants), len(mutant_keys)))
if mutant_keys != tag_key_set:
    fail("mutant keys != tag keys")

matrix_files = sorted(glob.glob(MATRIX_GLOB))
if not matrix_files:
    fail("no matrix shard files found")
matrix_keys: set[tuple[str, str]] = set()
matrix_seeds: set[str] = set()
matrix_horizons: set[str] = set()
matrix_rows = 0
for path in matrix_files:
    if ".triggers." in os.path.basename(path):
        continue
    rows = read_csv(Path(path))
    matrix_rows += len(rows)
    for r in rows:
        matrix_keys.add((r["task_id"], r["error_type"]))
        matrix_seeds.add(str(r["seeds"]).strip())
        matrix_horizons.add(str(r["horizon"]).strip())
if matrix_keys != tag_key_set:
    missing = sorted(tag_key_set - matrix_keys)[:8]
    extra = sorted(matrix_keys - tag_key_set)[:8]
    fail("matrix keys != tag keys; missing=%s extra=%s" % (missing, extra))
if matrix_seeds != {"10"}:
    fail("matrix seeds=%s, expected ['10']" % sorted(matrix_seeds))
if not matrix_horizons <= {"40000", "40000.0"}:
    fail("matrix horizons=%s" % sorted(matrix_horizons))

# E07 definition collapse: mmc-05 has lambda == mu.
e07 = [r for r in tags if r["task_id"] == "mmc-05" and r["error_type"] == "E07"]
if len(e07) != 1:
    fail("mmc-05/E07 rows=%d, expected 1" % len(e07))
p5 = task_params["mmc-05"]["params"]
if p5["lambda"] != p5["mu"]:
    fail("mmc-05 lambda=%r mu=%r; E07 is not a no-op" % (p5["lambda"], p5["mu"]))
if e07[0]["tag_strict_A"] != "MISS":
    fail("mmc-05/E07 tag=%s, expected MISS (definition collapse)" % e07[0]["tag_strict_A"])

# Theorem report.
theorem_text = THEOREM.read_text(encoding="utf-8")
m = re.search(r"总预测格\s*(\d+)，不吻合\s*(\d+)", theorem_text)
if not m:
    fail("cannot find '总预测格 ..., 不吻合 ...' in theorem report")
total_pred, total_bad = int(m.group(1)), int(m.group(2))
mismatch_pat = re.compile(
    r"- \[P2\] (E\d+)/([LW])@(\w+)\(([^)]+)\) 预测可检 实测不点火"
    r"\(rel 最大 ([\d.eE+-]+), τ\*=([\d.]+)\)"
)
mismatches: list[dict] = []
for line in theorem_text.splitlines():
    mm = mismatch_pat.search(line)
    if mm:
        tid = mm.group(4)
        pp = task_params.get(tid, {}).get("params", {})
        mismatches.append({
            "task_id": tid, "error_type": mm.group(1), "observable": mm.group(2),
            "template": mm.group(3), "c": pp.get("c"), "K": pp.get("K"),
            "lambda": pp.get("lambda"), "mu": pp.get("mu"),
            "rel_max": float(mm.group(5)), "tau": float(mm.group(6)),
            "prediction": "detectable", "observed": "not_fired", "verdict": "MISMATCH",
        })
if len(mismatches) != total_bad:
    fail("parsed %d mismatch rows, expected %d" % (len(mismatches), total_bad))

# P1-P4 summary rows.
prop_rows = []
for line in theorem_text.splitlines():
    if re.match(r"\| P[1-4] \|", line):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        prop_rows.append(cells)

# ------------------------------------------------------ analysis tags
analysis_rows = []
for r in tags:
    a = dict(r)
    if r["task_id"] == "mmc-05" and r["error_type"] == "E07":
        a["analysis_tag"] = COLLAPSE
        a["exclude_reason"] = "lambda_eq_mu_swap_noop"
    else:
        a["analysis_tag"] = r["tag_strict_A"]
        a["exclude_reason"] = ""
    analysis_rows.append(a)
write_csv(OUT_ANALYSIS, analysis_rows,
          ["task_id", "error_type", "template", "family", "expected_declared",
           "tag_strict_A", "fired_A", "rows", "no_tau", "ran",
           "analysis_tag", "exclude_reason"])

# ------------------------------------------------------ cluster bounds
cluster_rows = []
cluster_md = []
for cat in CATS:
    sub = [r for r in analysis_rows if r["expected_declared"] == cat]
    idle = [r for r in sub if r["analysis_tag"] == "INJECTION_IDLE"]
    noinst = [r for r in sub if r["analysis_tag"] == "NA_NOINST"]
    collapse = [r for r in sub if r["analysis_tag"] == COLLAPSE]
    raw_judged = [r for r in sub if r["analysis_tag"] not in EXCLUDE_TAGS]
    eff_judged = [r for r in raw_judged if r["analysis_tag"] != COLLAPSE]
    ok_tag = OK_TAG[cat]
    raw_succ = [r for r in raw_judged if r["tag_strict_A"] == ok_tag]
    raw_fail = [r for r in raw_judged if r["tag_strict_A"] != ok_tag]
    eff_fail = [r for r in eff_judged if r["tag_strict_A"] != ok_tag]
    # task clusters, raw and effective
    raw_tasks = {r["task_id"] for r in raw_judged}
    raw_fail_tasks = {r["task_id"] for r in raw_fail}
    eff_tasks = {r["task_id"] for r in eff_judged}
    eff_fail_tasks = {r["task_id"] for r in eff_fail}
    idle_only_tasks = {r["task_id"] for r in sub if r["analysis_tag"] == "INJECTION_IDLE"} - raw_tasks
    n, k = len(raw_judged), len(raw_fail)
    _, hi = wilson(k, n)
    tn, tk = len(raw_tasks), len(raw_fail_tasks)
    _, thi = wilson(tk, tn) if tn else (0.0, 1.0)
    en, ek = len(eff_judged), len(eff_fail)
    _, ehi = wilson(ek, en)
    etn, etk = len(eff_tasks), len(eff_fail_tasks)
    _, ethi = wilson(etk, etn) if etn else (0.0, 1.0)
    cluster_rows.append(dict(
        category=cat, declared=len(sub), idle=len(idle), noinst=len(noinst),
        collapse=len(collapse), judged=n, success=len(raw_succ), failure=k,
        artifact_fail_rate=("%.6f" % (k / n)) if n else "",
        artifact_wilson_hi=("%.6f" % hi) if n else "",
        judged_tasks=tn, failed_tasks=tk,
        idle_only_tasks=len(idle_only_tasks),
        task_fail_rate=("%.6f" % (tk / tn)) if tn else "",
        task_wilson_hi=("%.6f" % thi) if tn else "",
        eff_judged=en, eff_success=len(raw_succ), eff_failure=ek,
        eff_artifact_fail_rate=("%.6f" % (ek / en)) if en else "",
        eff_artifact_wilson_hi=("%.6f" % ehi) if en else "",
        eff_judged_tasks=etn, eff_failed_tasks=etk,
        eff_task_fail_rate=("%.6f" % (etk / etn)) if etn else "",
        eff_task_wilson_hi=("%.6f" % ethi) if etn else "",
    ))
    cluster_md.append([cat, str(len(sub)), str(len(idle)), str(len(noinst)),
                       str(len(collapse)), str(n), "%d/%d" % (len(raw_succ), n),
                       pct(hi), "%d/%d" % (tk, tn), pct(thi),
                       str(en), "%d/%d" % (len(raw_succ), en), pct(ehi),
                       "%d/%d" % (etk, etn), pct(ethi),
                       "%d" % len(idle_only_tasks)])

write_csv(OUT_CLUSTER, cluster_rows, list(cluster_rows[0].keys()))

# ------------------------------------------------------ per-cell n/CI
cell_groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
for r in analysis_rows:
    cell_groups[(r["template"], r["family"], r["expected_declared"])].append(r)
cell_rows = []
for (tpl, fam, cat), sub in sorted(cell_groups.items()):
    idle = sum(1 for r in sub if r["analysis_tag"] == "INJECTION_IDLE")
    noinst = sum(1 for r in sub if r["analysis_tag"] == "NA_NOINST")
    collapse = sum(1 for r in sub if r["analysis_tag"] == COLLAPSE)
    judged = [r for r in sub if r["analysis_tag"] not in EXCLUDE_TAGS | {COLLAPSE}]
    ok_tag = OK_TAG[cat]
    succ = sum(1 for r in judged if r["analysis_tag"] == ok_tag)
    failr = len(judged) - succ
    n = len(judged)
    lo, hi = wilson(succ, n) if n else (0.0, 1.0)
    cell_rows.append(dict(
        template=tpl, family=fam, category=cat, declared=len(sub), idle=idle,
        noinst=noinst, collapse=collapse, judged=n, success=succ, failure=failr,
        rate=("%.6f" % (succ / n)) if n else "",
        wilson_lo=("%.6f" % lo) if n else "", wilson_hi=("%.6f" % hi) if n else "",
        under_powered=1 if n <= 6 else 0,
        no_judged=1 if n == 0 else 0,
    ))
write_csv(OUT_CELL, cell_rows, list(cell_rows[0].keys()))

# ------------------------------------------------------ theorem mismatches
write_csv(OUT_THEOREM, mismatches, list(mismatches[0].keys()) if mismatches else
          ["task_id", "error_type", "observable", "template", "c", "K",
           "lambda", "mu", "rel_max", "tau", "prediction", "observed", "verdict"])

# ------------------------------------------------------ markdown
lines = ["# Full-64 统计包（64 题 / 1348 件）", "",
         "- 输入：`MUTANT_TAGS_full64.csv`（%d 行）、`BENIGN_PROOF_full64.csv`（%d 行）、"
         "`mutants_all64.jsonl`（%d 条）、`UNDETECTABILITY_MATRIX_full64.md`。"
         % (len(tags), len(ben), len(mutants)),
         "- 矩阵：%d 个分片，%d 行；工件键与 tags 全等；seeds=%s，horizon=%s。"
         % (len(matrix_files), matrix_rows, sorted(matrix_seeds), sorted(matrix_horizons)),
         "- 预算：R=10，H=40,000；这些数不替代 26 题 R10c 预注册子集。", "",
         "## 0. 完整性闸", "",
         "- tags=%d，唯一键=%d，题数=%d；benign=%d（%d 题，全部 PROVES_BENIGN）；"
         "mutants=%d；ran≠1 的件=%d（单列为 NA/CRASH，不混入判据分母）。"
         % (len(tags), len(set(tag_keys)), len(tasks), len(ben),
            len(ben_tasks), len(mutants), len(norun)),
         "- 标签：`%s`。" % json.dumps(dict(tag_counts), ensure_ascii=False, sort_keys=True),
         "- E07：mmc-05 的 λ=μ=%r；该件按定义塌缩剔除，原标签保留为 MISS。"
         % (p5["lambda"],), "",
         "## 1. 题簇上界（主表）", "",
         md_table(["类别", "声明", "IDLE", "无实例", "塌缩", "raw 可判", "raw 确认",
                   "raw 失败 Wilson 上界", "raw 题簇失败", "raw 题簇上界",
                   "eff 可判", "eff 确认", "eff 失败 Wilson 上界",
                   "eff 题簇失败", "eff 题簇上界", "仅 IDLE 题"], cluster_md), "",
         "读法：工件级是 1348 件里的比例；题簇级是“换一道同类新题”的保守上界。"
         "`NA_NOINST` 表示该件没有任何可判实例（不是“判过”），必须与 IDLE 分开报。", "",
         "## 2. 每格 n/CI", ""]
n_cells = len(cell_rows)
n_under = sum(1 for r in cell_rows if r["under_powered"])
n_over10 = sum(1 for r in cell_rows if r["judged"] >= 10)
n_none = sum(1 for r in cell_rows if r["no_judged"])
n_100 = sum(1 for r in cell_rows if r["judged"] and r["failure"] == 0)
lines += ["- 共 **%d** 个 `template×family×category` 格；**%d** 格 `judged≤6`；"
          "**%d** 格 `judged≥10`；**%d** 格无可判工件；**%d** 格 0 失败。"
          % (n_cells, n_under, n_over10, n_none, n_100),
          "- 全表见 `P4_cell_n_full64.csv`；`judged≤6` 的格只能写“点着了 n 件”，"
          "不能写“该格 100%% 可检”。", "",
          "## 3. E07 定义塌缩", "",
          "- `mmc-05`：λ=μ=%r，E07 交换两个相等速率 ⇒ 与 REF 行为不可区分。" % (p5["lambda"],),
          "- raw 与 eff 两套账见第 1 节；正文必须同时写 raw 的 MISS 和剔除后的 eff，"
          "不许静默把 raw 改成 100%%。", "",
          "## 4. 定理对账", "",
          "- 总预测 **%d** 格，不吻合 **%d** 格。" % (total_pred, total_bad)]
if mismatches:
    lines += ["- 全部不吻合：`%s`。" % ", ".join(
        "%s/%s@%s(c=%s,K=%s)" % (m["error_type"], m["observable"], m["task_id"],
                                  m["c"], m["K"]) for m in mismatches),
        "- rel 最大范围 **%.5g–%.5g**，全部低于 τ*。" % (
            min(m["rel_max"] for m in mismatches), max(m["rel_max"] for m in mismatches)),
        "- 逐行见 `P4_theorem_mismatches_full64.csv`。"]
if prop_rows:
    lines += ["", md_table(["命题", "预测格", "吻合", "不吻合", "分布"],
                            [[c[0], c[1], c[2], c[3], c[4]] for c in prop_rows])]
lines += ["", "## 5. 能写 / 禁写", "",
          "能写：",
          "- “full64：可检 %d/%d（raw）；剔除 E07 定义塌缩后 %d/%d（eff）。”"
          % (cluster_rows[0]["success"], cluster_rows[0]["judged"],
             cluster_rows[0]["eff_success"], cluster_rows[0]["eff_judged"]),
          "- “良性 0/%d 工件级（Wilson 上界 %s）；题簇级 0/%d（上界 %s）。”"
          % (cluster_rows[3]["judged"], pct(float(cluster_rows[3]["artifact_wilson_hi"])),
             cluster_rows[3]["judged_tasks"], pct(float(cluster_rows[3]["task_wilson_hi"]))),
          "- “定理 %d 格中 %d 格不吻合，全部 mmcK E03/E24，rel<τ*。”"
          % (total_pred, total_bad),
          "",
          "禁写：",
          "- ❌ “64 题全覆盖”如果不带“1348 件里有 %d 件无可判实例”的说明。" % (
              sum(1 for r in analysis_rows if r["analysis_tag"] == "NA_NOINST")),
          "- ❌ “良性 0/%d 所以假阳率 ≤%s”不带题簇上界。"
          % (cluster_rows[3]["judged"], pct(float(cluster_rows[3]["artifact_wilson_hi"]))),
          "- ❌ “定理 100%% 命中”。", ""]

OUT_MD.write_text("\n".join(lines), encoding="utf-8")
print("wrote %s" % OUT_MD)
print("wrote %s %s %s %s" % (OUT_CLUSTER, OUT_CELL, OUT_THEOREM, OUT_ANALYSIS))
print("tags=%s" % json.dumps(dict(tag_counts), ensure_ascii=True, sort_keys=True))
for r in cluster_rows:
    print(r["category"], "judged=%s success=%s failure=%s tasks=%s failed_tasks=%s"
          % (r["judged"], r["success"], r["failure"], r["judged_tasks"], r["failed_tasks"]))
print("theorem=%d/%d" % (total_pred, total_bad))
