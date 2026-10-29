#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare Qwen3.8-Flash full64 against DeepSeek-Flash full64.

Both arms: 64 tasks x 3 samples = 192 artifacts, same prompt, R=10/H=40000.
The Qwen sidecar is produced by rejudge_existing.py --shard on the full64 dir.
"""
from __future__ import annotations

import csv
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
BENCH = EXP.parent
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(HERE))

import LEGB_ARMS3 as A  # noqa: E402
import rejudge_existing as R  # noqa: E402
import criteria as C  # noqa: E402

QWEN_DIR = HERE / "qwen3.8flash_20261019_full64"
FLASH_DIR = BENCH / "legB" / "flash20261018"
QWEN_SIDES = sorted(glob.glob(str(QWEN_DIR / "_shard*.tsvl")))
FLASH_SIDE = BENCH / "_rejudge_flash20261018_v2.txt"
QWEN_MAN = QWEN_DIR / "manifest.jsonl"
FLASH_MAN = BENCH / "legB" / "legB_flash20261018.jsonl"
OUT_MD = HERE / "QWEN_vs_FLASH_FULL64.md"
OUT_CSV = HERE / "QWEN_vs_FLASH_FULL64.csv"

IDS = {t["task_id"] for t in C.load_tasks()}
QWEN = [r for r in R.load_sidecars(QWEN_SIDES) if r.get("task_id") in IDS]
FLASH = [r for r in A.load(str(FLASH_SIDE)) if r.get("task_id") in IDS]


def stats(rs):
    return A.stats(rs)


def closed_event(rs):
    closed = [r for r in rs if r.get("template") in ("eoq", "newsvendor")]
    event = [r for r in rs if r.get("template") not in ("eoq", "newsvendor")]
    return stats(closed), stats(event)


def truncated(rs, man_path, qwen=False):
    man = {}
    for line in io.open(man_path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        key = r.get("artifact") if qwen else r.get("file")
        if key:
            man[key] = r
    out = []
    for r in rs:
        m = man.get(r.get("file"))
        if not m:
            continue
        if "TRUNCATED" in str(m.get("err") or "") or str(m.get("finish") or "") == "length":
            out.append(r)
    return out


def wl_hits(rs, d):
    hit = n = 0
    for r in rs:
        p = os.path.join(d, r.get("file") or "")
        if not os.path.exists(p):
            continue
        n += 1
        code = io.open(p, encoding="utf-8", errors="ignore").read()
        if re.search(r"\bW\s*=\s*L\s*/", code):
            hit += 1
    return hit, n


def pct(a, b):
    return "—" if not b else "%.1f%%" % (100.0 * a / b)


def line(name, f, q):
    return "| %s | %s | %s |" % (name, f, q)


def main():
    if len(QWEN) != 192:
        raise SystemExit("Qwen sidecar records=%d, expected 192" % len(QWEN))
    if len(FLASH) != 192:
        raise SystemExit("Flash records=%d, expected 192" % len(FLASH))
    fs, qs = stats(FLASH), stats(QWEN)
    fc, fe = closed_event(FLASH)
    qc, qe = closed_event(QWEN)
    ftr = truncated(FLASH, FLASH_MAN, qwen=False)
    qtr = truncated(QWEN, QWEN_MAN, qwen=True)
    fw, fwn = wl_hits(FLASH, str(FLASH_DIR))
    qw, qwn = wl_hits(QWEN, str(QWEN_DIR))
    ft = dict((r[0], r) for r in A.by_template(FLASH))
    qt = dict((r[0], r) for r in A.by_template(QWEN))
    tpls = sorted(set(ft) | set(qt))
    L = []
    def w(s=""):
        L.append(s)

    w("# Qwen vs DeepSeek-Flash：全 64 题 × 3 抽\n")
    w("- 两边都是 192 件（64 题 × 3 抽）；同一 prompt、R=10/40000、max_tokens=4000。")
    w("- Qwen 侧判分：`rejudge_existing.py` 4 分片；Qwen 的 TRUNCATED 取生成侧 manifest，单列。\n")
    w("## 总表\n")
    w("| 指标 | DeepSeek-Flash | Qwen3.8-Flash |")
    w("|---|---:|---:|")
    w(line("件数", fs["n"], qs["n"]))
    w(line("可编译", "%d = %s" % (fs["compilable"], pct(fs["compilable"], fs["n"])),
           "%d = %s" % (qs["compilable"], pct(qs["compilable"], qs["n"]))))
    w(line("OK", "%d = %s" % (fs["ok"], pct(fs["ok"], fs["n"])),
           "%d = %s" % (qs["ok"], pct(qs["ok"], qs["n"]))))
    for k in ("NO_ENTRY", "CRASH", "SYNTAX", "FIELD_GAP"):
        w(line(k, fs["kinds"].get(k, 0), qs["kinds"].get(k, 0)))
    w(line("TRUNCATED(生成侧)", "%d = %s" % (len(ftr), pct(len(ftr), fs["n"])),
           "%d = %s" % (len(qtr), pct(len(qtr), qs["n"]))))
    w(line("字段齐全", "%d = %s" % (fs["complete"], pct(fs["complete"], fs["n"])),
           "%d = %s" % (qs["complete"], pct(qs["complete"], qs["n"]))))
    w(line("格级一致", "%d/%d = %s" % (fs["cell_in"], fs["cell_tot"], pct(fs["cell_in"], fs["cell_tot"])),
           "%d/%d = %s" % (qs["cell_in"], qs["cell_tot"], pct(qs["cell_in"], qs["cell_tot"]))))
    w(line("Qwen/Flash 覆盖率", "—", "%d/%d = %s" % (qs["cell_tot"], fs["cell_tot"], pct(qs["cell_tot"], fs["cell_tot"]))))
    w(line("件级全一致", "%d/%d = %s" % (fs["item_all"], fs["item_with_cells"], pct(fs["item_all"], fs["item_with_cells"])),
           "%d/%d = %s" % (qs["item_all"], qs["item_with_cells"], pct(qs["item_all"], qs["item_with_cells"]))))
    w(line("闭式格级", "%d/%d = %s" % (fc["cell_in"], fc["cell_tot"], pct(fc["cell_in"], fc["cell_tot"])),
           "%d/%d = %s" % (qc["cell_in"], qc["cell_tot"], pct(qc["cell_in"], qc["cell_tot"]))))
    w(line("事件驱动格级", "%d/%d = %s" % (fe["cell_in"], fe["cell_tot"], pct(fe["cell_in"], fe["cell_tot"])),
           "%d/%d = %s" % (qe["cell_in"], qe["cell_tot"], pct(qe["cell_in"], qe["cell_tot"]))))
    w(line("W=L/ 代码命中", "%d/%d" % (fw, fwn), "%d/%d" % (qw, qwn)))
    w("")
    w("## 按模板：格级一致（in/tot）\n")
    w("| 模板 | DeepSeek-Flash | Qwen3.8-Flash |")
    w("|---|---:|---:|")
    for t in tpls:
        f = ft.get(t)
        q = qt.get(t)
        fv = "—" if not f else "%d/%d" % (f[4], f[5])
        qv = "—" if not q else "%d/%d" % (q[4], q[5])
        w("| %s | %s | %s |" % (t, fv, qv))
    w("")
    w("## 读法")
    w("- 两边同 64 题、同 192 件；这是全量对称比较，不是 20 题子集。")
    w("- Qwen 的覆盖率 = Qwen 可判格 / Flash 可判格；Qwen 的 50% 类数字必须与这个覆盖率一起报。")
    w("- TRUNCATED 是生成侧，不混进判定侧 NO_ENTRY/CRASH；两边单列。")
    w("- `W=L/` 是代码级自证迹象，不是语义错。")
    with io.open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    with io.open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["metric", "flash", "qwen"])
        for row in L:
            if row.startswith("| ") and not row.startswith("|---") and "指标" not in row:
                cells = [c.strip() for c in row.strip("|").split("|")]
                if len(cells) == 3:
                    wr.writerow(cells)
    print("OK ->", OUT_MD)
    print("flash:", fs["kinds"], "cells", fs["cell_in"], "/", fs["cell_tot"], "trunc", len(ftr))
    print("qwen :", qs["kinds"], "cells", qs["cell_in"], "/", qs["cell_tot"], "trunc", len(qtr))


if __name__ == "__main__":
    main()
