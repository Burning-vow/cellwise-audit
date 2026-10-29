# -*- coding: utf-8 -*-
"""Overnight orchestrator: wait for the long jobs, then run every downstream step.

It is deliberately conservative: it only starts a downstream step when its
input coverage is complete.  If a timeout is hit, it records what was missing
and still runs the steps whose inputs are ready.
"""
from __future__ import annotations

import csv
import glob
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent
EXP = HERE.parent
PY = sys.executable
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
OUT = HERE / "OVERNIGHT_REPORT.md"
LOG = HERE / "overnight_orchestrator.log"

MISSING_KEYS = 1348
QWEN_OK = 128
EXT_REF = EXP / "external" / "EXTERNAL_REF_CHECK.csv"


def log(msg):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def matrix_keys():
    keys = set()
    for p in glob.glob(str(HERE / "MUTANT_MATRIX_full64.shard*.csv")):
        if ".triggers." in os.path.basename(p):
            continue
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("task_id") and r.get("error_type"):
                    keys.add((r["task_id"], r["error_type"]))
    return keys


def qwen_records():
    n = 0
    for p in glob.glob(str(EXP / "second_model" / "qwen3.8flash_20261019_full64" / "_shard[0-7].tsvl")):
        with open(p, encoding="utf-8") as f:
            n += sum(1 for l in f if l.strip())
    return n


def wait_for(name, cond, timeout=14400, interval=60):
    t0 = time.time()
    while True:
        try:
            ok = cond()
        except Exception as ex:
            log("%s check error: %s" % (name, ex))
            ok = False
        if ok:
            log("%s ready (%.0fs)" % (name, time.time() - t0))
            return True
        if time.time() - t0 > timeout:
            log("%s TIMEOUT after %ds" % (name, timeout))
            return False
        time.sleep(interval)


def run(name, args, timeout=3600):
    log("RUN %s: %s" % (name, " ".join(args)))
    t0 = time.time()
    p = subprocess.run(args, cwd=str(BENCH.parent), env=ENV,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    dt = time.time() - t0
    log("END %s rc=%s %.0fs" % (name, p.returncode, dt))
    if p.returncode != 0:
        log("STDERR %s: %s" % (name, (p.stderr or "")[-1200:]))
        log("STDOUT %s: %s" % (name, (p.stdout or "")[-1200:]))
    return p.returncode


def ext_ref_ok():
    if not EXT_REF.exists():
        return False
    with open(EXT_REF, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return len(rows) == 12 and all(r.get("verdict") == "PASS" for r in rows)


def ext_matrix_done():
    files = sorted(glob.glob(str(EXP / "external" / "EXTERNAL_MATRIX*.csv")))
    keys = set()
    for p in files:
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("task_id") and r.get("error_type"):
                    keys.add((r["task_id"], r["error_type"]))
    return len(keys) >= 77


def main():
    log("orchestrator start")
    full_ok = wait_for("full64 matrix 1348 keys", lambda: len(matrix_keys()) >= MISSING_KEYS)
    qwen_ok = wait_for("Qwen 128 complete-artifact sidecars", lambda: qwen_records() >= QWEN_OK)
    ext_ok = wait_for("external REF 12/12 PASS", ext_ref_ok, timeout=7200)

    results = {}
    if full_ok:
        results["summary"] = run("full64 summary", [PY, str(HERE / "run_summary_full64.py")], 1800)
        results["undetect"] = run("full64 theorem", [PY, str(HERE / "run_undetect_full64.py")], 1800)
        results["stats"] = run("full64 stats", [PY, str(HERE / "P4_full64_stats.py")], 600)
    else:
        log("skip full64 downstream: keys=%d" % len(matrix_keys()))

    if ext_ok:
        # A manual matrix process may already be running; wait for it instead of
        # starting a second writer on the same CSV.
        if not wait_for("external matrix 77 keys", ext_matrix_done, timeout=5400):
            results["ext_matrix"] = run("external matrix",
                                        [PY, str(EXP / "external" / "run_external.py"), "matrix", "1/1"],
                                        5400)
        results["ext_summary"] = run("external summary",
                                     [PY, str(EXP / "external" / "run_external.py"), "summary"], 300)
    else:
        log("skip external matrix: REF check incomplete")

    if qwen_ok:
        results["qwen"] = run("Qwen full64 coverage",
                              [PY, str(EXP / "second_model" / "summarize_qwen_full64.py")], 600)
    else:
        log("skip Qwen coverage: sidecars=%d" % qwen_records())

    lines = ["# Overnight report", "",
             "- full64 matrix keys: %d/%d" % (len(matrix_keys()), MISSING_KEYS),
             "- Qwen complete-artifact sidecars: %d/%d" % (qwen_records(), QWEN_OK),
             "- external REF CSV: %s" % (EXT_REF.exists()),
             "", "## Step return codes", ""]
    for k, v in results.items():
        lines.append("- %s: rc=%s" % (k, v))
    lines += ["", "## Files", "",
              "- `P4_full64_stats.md`", "- `MUTANT_SUMMARY_full64.md`",
              "- `UNDETECTABILITY_MATRIX_full64.md`", "- `EXTERNAL_SUMMARY.md`",
              "- `QWEN_FULL64_COVERAGE.md`", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    log("wrote %s" % OUT)
    log("orchestrator done")


if __name__ == "__main__":
    main()
