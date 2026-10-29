#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize the 17-artifact Qwen retry (first pass vs retry).

This is a sensitivity analysis, not a replacement for the main 20x3 arm.
"""
from __future__ import annotations

import csv
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent
sys.path.insert(0, str(BENCH))

import rejudge_existing as R  # noqa: E402

FIRST_DIR = HERE / "qwen3.8flash_20261019"
RETRY_DIR = HERE / "qwen3.8flash_20261019_retry17"
PLAN = HERE / "RETRY17_PLAN.csv"
RETRY_MAN = RETRY_DIR / "manifest.jsonl"
OUT_MD = HERE / "RETRY17_RESULT.md"
OUT_CSV = HERE / "RETRY17_RESULT.csv"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def main() -> None:
    plan = list(csv.DictReader(open(PLAN, encoding="utf-8-sig")))
    first = {
        r["file"]: r
        for r in R.load_sidecars(sorted(glob.glob(str(FIRST_DIR / "_qwen_shard*.tsvl"))))
        if r.get("file")
    }
    retry = {
        r["file"]: r
        for r in R.load_sidecars(sorted(glob.glob(str(RETRY_DIR / "_shard*.tsvl"))))
        if r.get("file")
    }
    man = {r.get("artifact"): r for r in load_jsonl(RETRY_MAN) if r.get("artifact")}
    # The retry files are named <tid>__d<sample>__retry.py; the first-pass
    # sidecar uses <tid>__d<sample>.py.
    rows = []
    for p in plan:
        f = p["file"]
        rf = f.replace(".py", "__retry.py")
        fr = first.get(f, {})
        rr = retry.get(rf, {})
        m = man.get(rf, {})
        rows.append({
            "task_id": p["task_id"],
            "template": p["template"],
            "sample": p["sample"],
            "first_kind": fr.get("kind", p["first_kind"]),
            "first_n_in": fr.get("n_in", 0),
            "first_n_tot": fr.get("n_tot", 0),
            "first_has_entry": fr.get("has_entry", ""),
            "retry_kind": rr.get("kind", "GEN_FAIL"),
            "retry_n_in": rr.get("n_in", 0),
            "retry_n_tot": rr.get("n_tot", 0),
            "retry_has_entry": rr.get("has_entry", ""),
            "retry_missing": rr.get("missing_fields", []),
            "retry_finish": m.get("finish", ""),
            "retry_code_lines": m.get("code_lines", ""),
            "retry_err": (m.get("err") or ""),
            "retry_run_note": (rr.get("run_note") or "")[:160],
        })

    first_counts = Counter(r["first_kind"] for r in rows)
    retry_counts = Counter(r["retry_kind"] for r in rows)
    recovered = [r for r in rows if r["retry_kind"] == "OK"]
    still_bad = [r for r in rows if r["retry_kind"] != "OK"]
    first_cells_in = sum(int(r["first_n_in"] or 0) for r in rows)
    first_cells_tot = sum(int(r["first_n_tot"] or 0) for r in rows)
    retry_cells_in = sum(int(r["retry_n_in"] or 0) for r in rows)
    retry_cells_tot = sum(int(r["retry_n_tot"] or 0) for r in rows)
    missing = [r for r in rows if r["retry_kind"] == "GEN_FAIL"]

    by_tpl = defaultdict(lambda: Counter())
    for r in rows:
        by_tpl[r["template"]]["first"] += 1
        if r["retry_kind"] == "OK":
            by_tpl[r["template"]]["ok"] += 1
        else:
            by_tpl[r["template"]]["bad"] += 1

    fields = list(rows[0].keys())
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    lines = []
    lines.append("# Qwen 17 件重试（first pass vs max_tokens=8000 + strict JSON）\n")
    lines.append("- 重试集 = 15 NO_ENTRY + 10 TRUNCATED 的并集 = **17 件**（8 件截断同时是 NO_ENTRY；另 2 件截断是 SYNTAX）。")
    lines.append("- 协议：同模型/同 prompt/ temperature=0 / enable_thinking=false；`max_tokens=8000`，并追加“完整程序 + 最后一行唯一 JSON”。")
    lines.append("- **首跑与重试分开报**；重试是敏感性分析，不并入主 20×3 臂。\n")
    lines.append("## 1. 分型对比\n")
    lines.append("| 指标 | 首跑（17 件） | 重试（17 件） |")
    lines.append("|---|---:|---:|")
    lines.append(f"| OK | {first_counts.get('OK', 0)} | {retry_counts.get('OK', 0)} |")
    for k in ("NO_ENTRY", "CRASH", "SYNTAX", "FIELD_GAP", "NO_JSON", "GEN_FAIL"):
        lines.append(f"| {k} | {first_counts.get(k, 0)} | {retry_counts.get(k, 0)} |")
    lines.append(f"| 可判格 | {first_cells_in}/{first_cells_tot} | {retry_cells_in}/{retry_cells_tot} |")
    lines.append("")
    lines.append(f"- 恢复为 OK：**{len(recovered)}/17**；仍非 OK：**{len(still_bad)}/17**；未生成：**{len(missing)}/17**。")
    lines.append("")
    lines.append("## 2. 逐件\n")
    lines.append("| task | d | first | retry | first cells | retry cells | retry finish | code lines |")
    lines.append("|---|---:|---|---|---:|---:|---|---:|")
    for r in rows:
        lines.append(
            f"| {r['task_id']} | {r['sample']} | {r['first_kind']} | {r['retry_kind']} | "
            f"{r['first_n_in']}/{r['first_n_tot']} | {r['retry_n_in']}/{r['retry_n_tot']} | "
            f"{r['retry_finish']} | {r['retry_code_lines']} |"
        )
    lines.append("")
    lines.append("## 3. 按模板\n")
    lines.append("| 模板 | 件数 | 重试 OK | 重试非 OK |")
    lines.append("|---|---:|---:|---:|")
    for t in sorted(by_tpl):
        c = by_tpl[t]
        lines.append(f"| {t} | {c['first']} | {c['ok']} | {c['bad']} |")
    lines.append("")
    lines.append("## 4. 读法\n")
    lines.append("- 如果多数件恢复为 OK：首跑的 NO_ENTRY/TRUNCATED 主要是**输出预算/契约提示**问题，不是模型不会做；")
    lines.append("  但重试用的是 8000 token，主 20×3 仍是 4000 token 口径 ⇒ 主表不能换成重试结果，只能做敏感性分析。")
    lines.append("- 如果多数仍非 OK：契约失败是稳健的，主表的 coverage 62.3% 不是预算造成的假象。")
    lines.append("- 重试集的准确率不能与主 50.5% 直接比：这 17 件是首跑最难的契约失败件，选择偏置很强；只报“恢复率/可判格”。")
    lines.append("- 若重试把 mh2/jackson2 的洞补上，正文可以写“预算/提示敏感”；若没有，保留“无/少可比格”。")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_CSV}")
    print("first", dict(first_counts))
    print("retry", dict(retry_counts))
    print("recovered", len(recovered), "still_bad", len(still_bad), "missing", len(missing))
    print("cells first", first_cells_in, "/", first_cells_tot, "retry", retry_cells_in, "/", retry_cells_tot)


if __name__ == "__main__":
    main()
