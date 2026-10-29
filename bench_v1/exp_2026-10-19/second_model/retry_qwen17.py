#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retry the 17 Qwen artifacts that failed the output contract.

Retry set = 15 NO_ENTRY + the 2 truncated SYNTAX artifacts (union, not 25).
The first pass is never overwritten: retry artifacts go to
qwen3.8flash_20261019_retry17/ and the retry manifest is separate.

Protocol: same model / prompt / temperature=0 / enable_thinking=false, but
max_tokens=8000 and an explicit "one JSON line, complete program" suffix.

Key: read from QWEN_API_KEY only; the key is never printed, written, or put in a command line.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import io
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(HERE))

import criteria as C  # noqa: E402
import gen_legB as G  # noqa: E402
import gen_qwen as GQ  # noqa: E402

FIRST_DIR = HERE / "qwen3.8flash_20261019"
RETRY_DIR = HERE / "qwen3.8flash_20261019_retry17"
FIRST_MAN = FIRST_DIR / "manifest.jsonl"
RETRY_MAN = RETRY_DIR / "manifest.jsonl"
PLAN_CSV = HERE / "RETRY17_PLAN.csv"
MAXTOK = 8000


def get_key() -> tuple[str, str]:
    key = os.environ.get("QWEN_API_KEY", "").strip()
    if not key:
        raise SystemExit("QWEN_API_KEY is not set. Provide your own key; this script never "
                         "reads credentials from any file.")
    return key, "env"



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


def build_retry_set() -> list[dict]:
    sidecars = []
    for p in sorted(glob.glob(str(FIRST_DIR / "_qwen_shard*.tsvl"))):
        sidecars += load_jsonl(Path(p))
    man = {r.get("artifact"): r for r in load_jsonl(FIRST_MAN) if r.get("artifact")}
    by_file = {r["file"]: r for r in sidecars if r.get("file")}
    no_entry = [f for f, r in by_file.items() if r.get("kind") == "NO_ENTRY"]
    trunc = [
        f
        for f in by_file
        if (man.get(f, {}).get("finish") == "length")
        or ("TRUNCATED" in str(man.get(f, {}).get("err") or ""))
    ]
    retry_files = sorted(set(no_entry) | set(trunc))
    rows = []
    for f in retry_files:
        r = by_file[f]
        m = re.search(r"__d(\d+)\.py$", f)
        if not m:
            raise SystemExit(f"cannot parse sample from {f}")
        first = man.get(f, {})
        reason = []
        if f in no_entry:
            reason.append("NO_ENTRY")
        if f in trunc:
            reason.append("TRUNCATED")
        rows.append({
            "file": f,
            "task_id": r["task_id"],
            "template": r.get("template", ""),
            "sample": int(m.group(1)),
            "first_kind": r.get("kind", ""),
            "first_finish": first.get("finish", ""),
            "reason": "+".join(reason),
        })
    if len(rows) != 17:
        raise SystemExit(f"retry set={len(rows)}, expected 17")
    expected_no_entry = sum(1 for r in rows if "NO_ENTRY" in r["reason"])
    expected_trunc = sum(1 for r in rows if "TRUNCATED" in r["reason"])
    if expected_no_entry != 15 or expected_trunc != 10:
        raise SystemExit(
            f"retry composition changed: NO_ENTRY={expected_no_entry} TRUNCATED={expected_trunc}"
        )
    return rows


def prompt_for(task: dict) -> str:
    base = G.build_prompt(task)
    need = sorted(G.required_fields(task, "rejudge"))
    suffix = (
        "\n\nRETRY REQUIREMENTS (the previous attempt failed the output contract):\n"
        "- Return ONLY the complete Python program. No markdown fences, no explanations.\n"
        "- Include `if __name__ == \"__main__\":` and call the entry point.\n"
        "- The last stdout line must be exactly one JSON object with every required field: "
        + ", ".join(need) + ".\n"
        "- Do not print any other line to stdout. Do not truncate; finish the program.\n"
        "- Keep the code under about 350 lines; avoid long comments.\n"
    )
    return base + suffix


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--spend", action="store_true")
    a = ap.parse_args()

    rows = build_retry_set()
    with open(PLAN_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"retry set={len(rows)} (NO_ENTRY={sum('NO_ENTRY' in r['reason'] for r in rows)}, "
          f"TRUNCATED={sum('TRUNCATED' in r['reason'] for r in rows)})")
    for r in rows:
        print(f"  {r['task_id']} d{r['sample']} {r['first_kind']} {r['reason']}")
    print(f"wrote {PLAN_CSV}")
    if a.plan:
        return

    if not (a.spend and os.environ.get("QWEN_SPEND") == "yes"):
        raise SystemExit("spend guard: pass --spend and set QWEN_SPEND=yes")
    key, key_src = get_key()
    GQ.KEY = key
    GQ.MAXTOK = MAXTOK
    print(f"[retry] base={GQ.BASE} model={GQ.MODEL} key=set({key_src}) max_tokens={MAXTOK}", flush=True)

    RETRY_DIR.mkdir(parents=True, exist_ok=True)
    # Only successful generations are "done"; a network/SSL failure has no
    # artifact and must stay retryable.
    done = {
        (r["task_id"], r["sample"])
        for r in load_jsonl(RETRY_MAN)
        if r.get("artifact")
    }
    tasks = {t["task_id"]: t for t in C.load_tasks()}
    tot_in = tot_out = 0
    n = 0
    with open(RETRY_MAN, "a", encoding="utf-8") as f:
        for row in rows:
            tid, sample = row["task_id"], row["sample"]
            if (tid, sample) in done:
                continue
            task = tasks[tid]
            prompt = prompt_for(task)
            ph = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
            n += 1
            t0 = time.time()
            r = GQ.call_qwen(prompt)
            u = r.get("usage") or {}
            rec = {
                "task_id": tid, "template": task["template"], "sample": sample,
                "model": GQ.MODEL, "retry_of": row["file"],
                "first_kind": row["first_kind"], "first_finish": row["first_finish"],
                "prompt_sha16": ph, "wall": round(time.time() - t0, 1),
                "usage": u, "finish": r.get("finish"),
                "reasoning_len": r.get("reasoning_len"), "err": r.get("err"),
            }
            if r.get("text"):
                code = G.extract_code(r["text"])
                fn = RETRY_DIR / f"{tid}__d{sample}__retry.py"
                fn.write_text(code + "\n", encoding="utf-8")
                rec["artifact"] = fn.name
                rec["code_lines"] = len(code.splitlines())
            tot_in += int(u.get("prompt_tokens") or 0)
            tot_out += int(u.get("completion_tokens") or 0)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"[retry] {n} {tid} d{sample} {'OK' if r.get('text') else 'FAIL'} "
                  f"in={u.get('prompt_tokens')} out={u.get('completion_tokens')} "
                  f"wall={rec['wall']}s {str(r.get('err') or '')[:100]}", flush=True)
    print(f"[retry] calls={n} tokens_in={tot_in} tokens_out={tot_out} out={RETRY_DIR}", flush=True)


if __name__ == "__main__":
    main()
