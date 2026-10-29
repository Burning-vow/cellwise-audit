# -*- coding: utf-8 -*-
"""Three-arm 8k summary: DeepSeek-Flash / Qwen3.8-Flash / GLM-5.3-Flash.

The 20-task 4k paired table is a separate pilot; this script is the full64
8k comparison. It reports every arm and never drops one post-hoc.
"""
from __future__ import annotations

import csv
import glob
import io
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent
sys.path.insert(0, str(BENCH))
import LEGB_ARMS3 as A  # noqa: E402
import rejudge_existing as R  # noqa: E402

OUT_MD = HERE / "THREE_ARM_8K_TABLE.md"
OUT_CSV = HERE / "THREE_ARM_8K_TABLE.csv"

ARMS = {
    "DeepSeek-Flash": {
        "manifests": [BENCH / "legB" / "legB_flash20261020_8k.jsonl"],
        "sides": [str(BENCH / "legB" / "flash20261020_8k" / "_shard*.tsvl")],
        "artdirs": [BENCH / "legB" / "flash20261020_8k"],
    },
    "Qwen3.8-Flash": {
        "manifests": [HERE / ("qwen3.8flash_20261020_full64_8k_shard%d" % i) / "manifest.jsonl"
                      for i in (1, 2, 3)],
        "sides": [str(HERE / ("qwen3.8flash_20261020_full64_8k_shard%d" % i) / "_shard*.tsvl")
                  for i in (1, 2, 3)] + [str(HERE / "qwen3.8flash_20261020_full64_8k_remaining" / "_shard*.tsvl")],
        "artdirs": [HERE / ("qwen3.8flash_20261020_full64_8k_shard%d" % i) for i in (1, 2, 3)]
                   + [HERE / "qwen3.8flash_20261020_full64_8k_remaining"],
    },
    "GLM-5.3-Flash": {
        "manifests": [HERE / "glm53flash_20261020_full64_8k" / "manifest.jsonl"],
        "sides": [str(HERE / "glm53flash_20261020_full64_8k" / "_shard*.tsvl"),
                  str(HERE / "glm53flash_20261020_full64_8k_remaining" / "_shard*.tsvl")],
        "artdirs": [HERE / "glm53flash_20261020_full64_8k",
                    HERE / "glm53flash_20261020_full64_8k_remaining"],
    },
}


def load_manifest(paths):
    rows = []
    for p in paths:
        if not Path(p).exists():
            continue
        for line in io.open(p, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    return rows


def arm_stats(spec):
    rows = load_manifest(spec["manifests"])
    trunc = sum(1 for r in rows if r.get("truncated") or r.get("finish") == "length")
    err = sum(1 for r in rows if r.get("err") and not (r.get("truncated") or r.get("finish") == "length"))
    arts = {os.path.basename(p) for d in spec["artdirs"]
            for p in glob.glob(str(Path(d) / "*.py"))}
    side_paths = []
    for pat in spec["sides"]:
        side_paths += glob.glob(pat)
    recs = R.load_sidecars(sorted(side_paths)) if side_paths else []
    s = A.stats(recs) if recs else dict(n=0, kinds={}, compilable=0, entered=0, ok=0,
                                        complete=0, cell_in=0, cell_tot=0,
                                        item_all=0, item_with_cells=0)
    tin = sum(int((r.get("usage") or {}).get("prompt_tokens") or 0) for r in rows)
    tout = sum(int((r.get("usage") or {}).get("completion_tokens") or 0) for r in rows)
    treason = sum(int(r.get("reasoning_tokens") or 0) for r in rows)
    wall = sum(float(r.get("wall") or 0) for r in rows)
    return dict(rows=len(rows), artifacts=len(arts), trunc=trunc, err=err,
                gen_complete=len(arts) - trunc,
                runtime_n=s["n"], kinds=json.dumps(s["kinds"], ensure_ascii=False, sort_keys=True),
                compilable=s["compilable"], entered=s["entered"], ok=s["ok"],
                obs_complete=s["complete"], cell_in=s["cell_in"], cell_tot=s["cell_tot"],
                item_all=s["item_all"], item_with_cells=s["item_with_cells"],
                tokens_in=tin, tokens_out=tout, reasoning=treason, wall=wall)


def pct(a, b):
    return "n/a" if not b else "%.1f%%" % (100.0 * a / b)


def main():
    stats = {name: arm_stats(spec) for name, spec in ARMS.items()}
    ds_cells = stats["DeepSeek-Flash"]["cell_tot"]
    lines = ["# Three-arm 8k comparison (full64)", "",
             "- 64 tasks × 3 samples per arm; same prompt; max_tokens=8000; temperature=0.",
             "- Runtime: R=10 seeds, H=40,000, same J1–J3/tau*.",
             "- All three arms are reported; no post-hoc arm selection.",
             "- The 20-task 4k pair is a separate pilot, not this table.", "",
             "| Arm | Gen complete/192 | Truncated | API/generation err | Compile | Entry | OK | Comparable cells | Cell agree | Coverage vs DS | Tokens in/out | Reasoning | Wall |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name, s in stats.items():
        lines.append("| %s | %d/192 | %d | %d | %d | %d | %d | %d | %s | %s | %d/%d | %d | %.1f s |"
                     % (name, s["artifacts"] - s["trunc"], s["trunc"], s["err"],
                        s["compilable"], s["entered"], s["ok"], s["cell_tot"],
                        pct(s["cell_in"], s["cell_tot"]),
                        pct(s["cell_tot"], ds_cells), s["tokens_in"], s["tokens_out"],
                        s["reasoning"], s["wall"]))
    lines += ["", "## Runtime kinds", ""]
    for name, s in stats.items():
        lines.append("- %s: `%s`; sidecar records=%d" % (name, s["kinds"], s["runtime_n"]))
    lines += ["", "## Notes", "",
              "- `Gen complete` = artifacts on disk minus `finish=length`; API errs are those with a non-length error.",
              "- `Coverage vs DS` = this arm's comparable cells / DeepSeek's comparable cells (not a same-key ratio unless the arms share every key; read with `Comparable cells`).",
              "- GLM-5.3-Flash cannot disable thinking; `reasoning` is its reasoning-token total, never counted as code.",
              "- A runtime CRASH/NO_ENTRY/SYNTAX is not a generation truncation; both are reported.",
              "- CSV columns: `gen_complete` = artifacts minus truncations (the `Gen complete` column here); "
              "`obs_complete` = sidecar records that emitted observations with no missing field. They are different "
              "quantities and must not be compared across files under one name.",
              ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        fields = ["arm", "rows", "artifacts", "trunc", "err", "runtime_n", "kinds",
                  "compilable", "entered", "ok", "gen_complete", "obs_complete", "cell_in", "cell_tot",
                  "item_all", "item_with_cells", "tokens_in", "tokens_out", "reasoning", "wall"]
        w.writerow(fields)
        for name, s in stats.items():
            w.writerow([name] + [s[f] for f in fields[1:]])
    print("wrote", OUT_MD)
    for name, s in stats.items():
        print(name, json.dumps(s, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
