# -*- coding: utf-8 -*-
"""Qwen3.8-Flash full64 coverage report.

Generation ran 64 tasks x 3 samples = 192. 64 generations are truncated at
4,000 tokens; those are a generation-side coverage limit and are not re-run as
if they were runtime bugs.  Runtime rejudge is performed on the 128
generation-complete artifacts.  This script reports both denominators and, for
the same 128 artifact keys, the Flash full64 sidecar as a paired reference.
"""
from __future__ import annotations

import csv
import glob
import io
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent
sys.path.insert(0, str(BENCH))
import LEGB_ARMS3 as A  # noqa: E402
import rejudge_existing as R  # noqa: E402

QWEN_DIR = HERE / "qwen3.8flash_20261019_full64"
MAN = QWEN_DIR / "manifest.jsonl"
SIDES = sorted(glob.glob(str(QWEN_DIR / "_shard[0-7].tsvl")))
FLASH = BENCH / "_rejudge_flash20261018_v2.txt"
OUT_MD = HERE / "QWEN_FULL64_COVERAGE.md"
OUT_CSV = HERE / "QWEN_FULL64_COVERAGE.csv"


def pct(a, b):
    return "n/a" if not b else "%.1f%%" % (100.0 * a / b)


def main():
    man = [json.loads(l) for l in io.open(MAN, encoding="utf-8") if l.strip()]
    if len(man) != 192:
        raise SystemExit("manifest=%d, expected 192" % len(man))
    bad = [r for r in man if "length" in str(r.get("finish")) or "length" in str(r.get("err"))]
    good = [r for r in man if r not in bad]
    if len(good) != 128:
        raise SystemExit("generation-complete=%d, expected 128" % len(good))
    recs = R.load_sidecars(SIDES)
    if len(recs) != 128:
        raise SystemExit("runtime sidecar records=%d, expected 128" % len(recs))
    qwen = A.stats(recs)
    flash = A.load(str(FLASH))
    qkeys = {r["file"] for r in recs}
    flash_same = [r for r in flash if r.get("file") in qkeys]
    fs = A.stats(flash_same)

    by_tpl_gen = defaultdict(lambda: [0, 0])
    for r in man:
        t = r.get("template") or "?"
        by_tpl_gen[t][1] += 1
        if r not in bad:
            by_tpl_gen[t][0] += 1

    lines = ["# Qwen3.8-Flash full64：生成覆盖 + 运行期重判", "",
             "- 生成：64 题 × 3 抽 = **192**；生成完整 **128**，截断 **64**（max_tokens=4000）。",
             "- 运行期重判只对 128 件生成完整件；64 件截断件不伪装成运行期错误。",
             "- 判分预算：R=10 / horizon=40000；与主表同口径。", "",
             "## 1. 生成覆盖（按模板）", "",
             "| template | complete / total | rate |", "|---|---:|---:|"]
    for t, (ok, n) in sorted(by_tpl_gen.items()):
        lines.append("| %s | %d/%d | %s |" % (t, ok, n, pct(ok, n)))
    lines += ["", "## 2. 运行期重判（128 件生成完整件）", "",
              "- 可编译：%d/%d = %s" % (qwen["compilable"], qwen["n"], pct(qwen["compilable"], qwen["n"])),
              "- 进入运行（有入口）：%d/%d" % (qwen["entered"], qwen["n"]),
              "- 契约字段齐全：%d/%d = %s" % (qwen["complete"], qwen["n"], pct(qwen["complete"], qwen["n"])),
              "- 类型分布：`%s`" % json.dumps(qwen["kinds"], ensure_ascii=False, sort_keys=True),
              "- 可比格：%d（件级全一致 %d/%d）" % (qwen["cell_in"] + qwen["cell_tot"] - qwen["cell_in"],
                                                qwen["item_all"], qwen["item_with_cells"]),
              "", "## 3. 同一 128 个工件键上的 Flash 对照", "",
              "| 指标 | Qwen3.8-Flash | DeepSeek-Flash |", "|---|---:|---:|",
              "| 件数 | %d | %d |" % (qwen["n"], fs["n"]),
              "| 可编译 | %d (%s) | %d (%s) |" % (qwen["compilable"], pct(qwen["compilable"], qwen["n"]),
                                                  fs["compilable"], pct(fs["compilable"], fs["n"])),
              "| OK | %d (%s) | %d (%s) |" % (qwen["ok"], pct(qwen["ok"], qwen["n"]),
                                               fs["ok"], pct(fs["ok"], fs["n"])),
              "| 契约齐全 | %d (%s) | %d (%s) |" % (qwen["complete"], pct(qwen["complete"], qwen["n"]),
                                                     fs["complete"], pct(fs["complete"], fs["n"])),
              "| 可比格 | %d | %d |" % (qwen["cell_tot"], fs["cell_tot"]),
              "| 格级一致 | %d/%d = %s | %d/%d = %s |" % (
                  qwen["cell_in"], qwen["cell_tot"], pct(qwen["cell_in"], qwen["cell_tot"]),
                  fs["cell_in"], fs["cell_tot"], pct(fs["cell_in"], fs["cell_tot"])),
              "", "读法：这 128 键是 Qwen 生成完整的子集，不是随机子集；Flash 的 128 件统计是"
              "同一子集上的参考，不是两边全量 192 件的配对。全量 192 件的 20 题配对结果见"
              "`QWEN_vs_FLASH_20TASKS.md`。", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["arm", "n", "compilable", "entered", "ok", "complete",
                    "cell_in", "cell_tot", "item_all", "item_with_cells"])
        for name, s in (("qwen128", qwen), ("flash_same128", fs)):
            w.writerow([name, s["n"], s["compilable"], s["entered"], s["ok"], s["complete"],
                        s["cell_in"], s["cell_tot"], s["item_all"], s["item_with_cells"]])
    print("wrote %s" % OUT_MD)
    print("qwen128", json.dumps(qwen, ensure_ascii=True, sort_keys=True))
    print("flash_same128", json.dumps(fs, ensure_ascii=True, sort_keys=True))
    print("generation", json.dumps(dict(by_tpl_gen), ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
