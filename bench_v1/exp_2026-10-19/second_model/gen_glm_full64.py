# -*- coding: utf-8 -*-
"""GLM-5.3-Flash full64 arm (official Zhipu API).

Protocol: same prompt as the Qwen/DeepSeek arms, 64 tasks x 3 samples,
temperature=0, max_tokens=4000. This model cannot disable thinking; we set
reasoning_effort=low and record reasoning tokens separately.

Key: read from QWEN_API_KEY only; the key is never printed, written, or put in a command line.
The key is never printed or written to disk.
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent.parent
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(HERE))

import criteria as C  # noqa: E402
import gen_legB as G  # noqa: E402

OUT_DIR = HERE / "glm53flash_20261020_full64"
MANIFEST = OUT_DIR / "manifest.jsonl"
BASE = "https://open.bigmodel.cn/api/paas/v4"
MODEL = "glm-5.3-flash"
MAXTOK = 4000
SAMPLES = 3


def get_key() -> tuple[str, str]:
    key = os.environ.get("QWEN_API_KEY", "").strip()
    if not key:
        raise SystemExit("QWEN_API_KEY is not set. Provide your own key; this script never "
                         "reads credentials from any file.")
    return key, "env"



def call_glm(prompt):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": G.SYS_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": MAXTOK,
        "reasoning_effort": "low",
    }
    body = json.dumps(payload).encode("utf-8")
    last = None
    for attempt in range(3):
        req = urllib.request.Request(BASE.rstrip("/") + "/chat/completions",
                                     data=body, method="POST")
        req.add_header("Authorization", "Bearer " + KEY)
        req.add_header("Content-Type", "application/json")
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                j = json.loads(resp.read().decode("utf-8"))
            ch = (j.get("choices") or [{}])[0]
            msg = ch.get("message") or {}
            u = j.get("usage") or {}
            text = msg.get("content") or ""
            out = {
                "text": text,
                "reasoning_len": len(msg.get("reasoning_content") or ""),
                "usage": u,
                "wall": time.time() - t0,
                "finish": ch.get("finish_reason"),
            }
            if not text.strip():
                out["err"] = "EMPTY_CONTENT"
            if out["finish"] == "length":
                out["err"] = (out.get("err") or "") + " TRUNCATED(finish=length)"
            return out
        except urllib.error.HTTPError as e:
            body_txt = e.read().decode("utf-8", "replace")[:300]
            last = "HTTP %s %s" % (e.code, body_txt)
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(5 * (attempt + 1))
                continue
            return {"err": last, "wall": time.time() - t0}
        except Exception as e:
            last = "%s: %s" % (type(e).__name__, e)
            time.sleep(3 * (attempt + 1))
    return {"err": last or "UNKNOWN", "wall": 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spend", action="store_true")
    a = ap.parse_args()
    tasks = C.load_tasks()
    if len(tasks) != 64:
        raise SystemExit("tasks=%d, expected 64" % len(tasks))
    if not (a.spend and os.environ.get("GLM_SPEND") == "yes"):
        raise SystemExit("spend guard: pass --spend and set GLM_SPEND=yes")
    global KEY
    KEY, key_src = get_key()
    OUT_DIR.mkdir(exist_ok=True)
    done = set()
    if MANIFEST.exists():
        for line in io.open(MANIFEST, encoding="utf-8"):
            try:
                r = json.loads(line)
                if r.get("artifact") and not r.get("truncated"):
                    done.add((r["task_id"], r["sample"]))
            except ValueError:
                pass
    fh = io.open(MANIFEST, "a", encoding="utf-8")
    tot_in = tot_out = tot_reason = 0
    n = 0
    print("[glm53] base=%s model=%s key=set(%s) max_tokens=%d done=%d"
          % (BASE, MODEL, key_src, MAXTOK, len(done)), flush=True)
    for task in tasks:
        tid = task["task_id"]
        prompt = G.build_prompt(task)
        ph = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
        for s in range(1, SAMPLES + 1):
            if (tid, s) in done:
                continue
            n += 1
            t0 = time.time()
            r = call_glm(prompt)
            u = r.get("usage") or {}
            rec = {
                "task_id": tid, "template": task["template"], "sample": s,
                "model": MODEL, "prompt_sha16": ph,
                "wall": round(time.time() - t0, 1), "usage": u,
                "finish": r.get("finish"), "reasoning_len": r.get("reasoning_len"),
                "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
                "err": r.get("err"),
                "truncated": r.get("finish") == "length",
            }
            if r.get("text"):
                code = G.extract_code(r["text"])
                fn = OUT_DIR / ("%s__d%d.py" % (tid, s))
                fn.write_text(code + "\n", encoding="utf-8", newline="\n")
                rec["artifact"] = fn.name
                rec["code_lines"] = len(code.splitlines())
            tot_in += int(u.get("prompt_tokens") or 0)
            tot_out += int(u.get("completion_tokens") or 0)
            tot_reason += int(rec.get("reasoning_tokens") or 0)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            print("[glm53] %d %s d%d %s in=%s out=%s reason=%s wall=%.1fs %s"
                  % (n, tid, s, "OK" if r.get("text") else "FAIL",
                     u.get("prompt_tokens"), u.get("completion_tokens"),
                     rec.get("reasoning_tokens"), rec["wall"], (r.get("err") or "")[:90]),
                  flush=True)
    fh.close()
    print("[glm53] calls=%d tokens_in=%d tokens_out=%d reasoning=%d out=%s"
          % (n, tot_in, tot_out, tot_reason, OUT_DIR), flush=True)


if __name__ == "__main__":
    main()
