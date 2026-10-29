#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qwen3.8-Flash on all 64 tasks x 3 samples (192 artifacts).

This is a fresh, symmetric full64 arm. It does not overwrite the existing
20-task arm. Protocol matches the first pass: same prompt, temperature 0,
enable_thinking false, max_tokens 4000. Network failures are retryable;
successful artifacts are skipped on resume.
"""
from __future__ import annotations

import argparse
import hashlib
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

OUT_DIR = HERE / "qwen3.8flash_20261020_full64_8k"
MANIFEST = OUT_DIR / "manifest.jsonl"
MAXTOK = 8000
SAMPLES = 3


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spend", action="store_true")
    ap.add_argument("--shard", default="1/1")
    a = ap.parse_args()
    i, nshard = [int(x) for x in a.shard.split("/")]
    if not (1 <= i <= nshard):
        raise SystemExit("bad --shard %s" % a.shard)
    tasks = C.load_tasks()
    all_ids = [t["task_id"] for t in tasks]
    if len(all_ids) != 64:
        raise SystemExit(f"tasks={len(all_ids)}, expected 64")
    tasks = tasks[i - 1::nshard]
    ids = [t["task_id"] for t in tasks]
    out_dir = HERE / ("qwen3.8flash_20261020_full64_8k_shard%d" % i)
    manifest = out_dir / "manifest.jsonl"
    if not (a.spend and os.environ.get("QWEN_SPEND") == "yes"):
        raise SystemExit("spend guard: pass --spend and set QWEN_SPEND=yes")
    key, key_src = get_key()
    GQ.KEY = key
    GQ.MAXTOK = MAXTOK
    print(f"[qwen-full64] base={GQ.BASE} model={GQ.MODEL} key=set({key_src}) "
          f"max_tokens={MAXTOK} shard={i}/{nshard} tasks={len(ids)} samples={SAMPLES}", flush=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    done = {
        (r["task_id"], r["sample"])
        for r in load_jsonl(manifest)
        if r.get("artifact")
    }
    by_id = {t["task_id"]: t for t in tasks}
    tot_in = tot_out = 0
    n = 0
    with open(manifest, "a", encoding="utf-8") as f:
        for tid in ids:
            task = by_id[tid]
            prompt = G.build_prompt(task)
            ph = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
            for s in range(1, SAMPLES + 1):
                if (tid, s) in done:
                    continue
                n += 1
                t0 = time.time()
                r = GQ.call_qwen(prompt)
                u = r.get("usage") or {}
                rec = {
                    "task_id": tid, "template": task["template"], "sample": s,
                    "model": GQ.MODEL, "prompt_sha16": ph,
                    "wall": round(time.time() - t0, 1), "usage": u,
                    "finish": r.get("finish"), "reasoning_len": r.get("reasoning_len"),
                    "err": r.get("err"),
                }
                if r.get("text"):
                    code = G.extract_code(r["text"])
                    fn = out_dir / f"{tid}__d{s}.py"
                    fn.write_text(code + "\n", encoding="utf-8")
                    rec["artifact"] = fn.name
                    rec["code_lines"] = len(code.splitlines())
                tot_in += int(u.get("prompt_tokens") or 0)
                tot_out += int(u.get("completion_tokens") or 0)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                print(f"[qwen-full64] {n} {tid} d{s} "
                      f"{'OK' if r.get('text') else 'FAIL'} "
                      f"in={u.get('prompt_tokens')} out={u.get('completion_tokens')} "
                      f"wall={rec['wall']}s {str(r.get('err') or '')[:100]}", flush=True)
    print(f"[qwen-full64] calls={n} tokens_in={tot_in} tokens_out={tot_out} out={out_dir}",
          flush=True)


if __name__ == "__main__":
    main()
