# -*- coding: utf-8 -*-
"""P2 第二模型生成端：Qwen3.8-Flash（跨家族 peer），20 题 × 3 抽。

用法：
  QWEN_API_KEY=... python gen_qwen.py --pilot=2        # 2 题 × 1 抽，只报价
  QWEN_API_KEY=... QWEN_SPEND=yes python gen_qwen.py --spend   # 20 题 × 3 抽

纪律：
  - key 只从环境变量读，不落盘、不打印；base/model 只回显。
  - prompt 复用 gen_legB.build_prompt（与 flash 臂同一套题面/字段/CLI），不把 params/真值喂给模型。
  - 每题 3 抽、temperature=0、enable_thinking=false；逐条 flush，按 (task,sample) 续跑。
  - 成本只报 token；价格按网关账单为准，脚本不编单价。
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

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)
import criteria as C  # noqa: E402
import gen_legB as G  # noqa: E402

OUT_DIR = os.path.join(HERE, 'qwen3.8flash_20261019')
MANIFEST = os.path.join(OUT_DIR, 'manifest.jsonl')
MODEL = os.environ.get('QWEN_MODEL', 'qwen3.8-flash')
BASE = os.environ.get('QWEN_BASE_URL', 'https://maas.qianwenaiapi.com/compatible-mode/v1')
KEY = os.environ.get('QWEN_API_KEY', '')
SPEND = os.environ.get('QWEN_SPEND') == 'yes'
MAXTOK = int(os.environ.get('QWEN_MAX_TOKENS', '4000'))


def pick_20():
    """14 排队（当前注入的 2/模板）+ 3 eoq + 3 newsvendor = 20；与 flash 臂同题子集。"""
    ms = [json.loads(l) for l in io.open(os.path.join(BENCH, 'mutants.jsonl'), encoding='utf-8')]
    by = {}
    for m in ms:
        by.setdefault(m['template'], set()).add(m['task_id'])
    q = []
    for tpl in ('mm1', 'mmc', 'mm1K', 'mmcK', 'md1', 'mh2', 'jackson2'):
        q += sorted(by.get(tpl, []))[:2]
    closed = sorted(by.get('eoq', []))[:3] + sorted(by.get('newsvendor', []))[:3]
    ids = q + closed
    assert len(ids) == 20, (len(ids), ids)
    return ids


def call_qwen(prompt):
    payload = {'model': MODEL,
               'messages': [{'role': 'system', 'content': G.SYS_PROMPT},
                            {'role': 'user', 'content': prompt}],
               'temperature': 0.0, 'max_tokens': MAXTOK,
               'enable_thinking': False}
    req = urllib.request.Request(BASE.rstrip('/') + '/chat/completions',
                                 data=json.dumps(payload).encode('utf-8'), method='POST')
    req.add_header('Authorization', 'Bearer ' + KEY)
    req.add_header('Content-Type', 'application/json')
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            j = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'err': 'HTTP %s %s' % (e.code, e.read().decode('utf-8', 'replace')[:300]),
                'wall': time.time() - t0}
    except Exception as e:
        return {'err': '%s: %s' % (type(e).__name__, e), 'wall': time.time() - t0}
    ch = (j.get('choices') or [{}])[0]
    msg = ch.get('message') or {}
    usage = j.get('usage') or {}
    text = msg.get('content') or ''
    out = {'text': text, 'reasoning_len': len(msg.get('reasoning_content') or ''),
           'usage': usage, 'wall': time.time() - t0, 'finish': ch.get('finish_reason')}
    if not text.strip():
        out['err'] = 'EMPTY_CONTENT'
    if out['finish'] == 'length':
        out['err'] = (out.get('err') or '') + ' TRUNCATED(finish=length)'
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pilot', type=int, default=0)
    ap.add_argument('--spend', action='store_true')
    ap.add_argument('--samples', type=int, default=3)
    a = ap.parse_args()
    if not KEY:
        raise SystemExit('QWEN_API_KEY 未设置；不打印 key，只停。')
    print('[qwen] base=%s model=%s key=set max_tokens=%d' % (BASE, MODEL, MAXTOK), flush=True)
    tasks = {t['task_id']: t for t in C.load_tasks()}
    ids = pick_20()
    if a.pilot:
        # 1 道排队 + 1 道闭式；闭式从 ids[14] 起（pick_20 前 14 是排队）
        ids = ([ids[0], ids[14]] if a.pilot >= 2 else ids[:a.pilot])
        samples = 1
    else:
        if not (a.spend and SPEND):
            raise SystemExit('花钱前必须同时给 --spend 且 QWEN_SPEND=yes；未花钱，停。')
        samples = a.samples
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    done = set()
    if os.path.exists(MANIFEST):
        for line in io.open(MANIFEST, encoding='utf-8'):
            try:
                r = json.loads(line)
                done.add((r['task_id'], r['sample']))
            except ValueError:
                pass
    tot_in = tot_out = 0
    fh = io.open(MANIFEST, 'a', encoding='utf-8')
    n = 0
    for tid in ids:
        task = tasks[tid]
        prompt = G.build_prompt(task)
        ph = hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]
        for s in range(1, samples + 1):
            if (tid, s) in done:
                continue
            n += 1
            t0 = time.time()
            r = call_qwen(prompt)
            rec = {'task_id': tid, 'template': task['template'], 'sample': s,
                   'model': MODEL, 'prompt_sha16': ph, 'wall': round(time.time() - t0, 1),
                   'usage': r.get('usage'), 'finish': r.get('finish'),
                   'reasoning_len': r.get('reasoning_len'), 'err': r.get('err')}
            if r.get('text'):
                code = G.extract_code(r['text'])
                fn = os.path.join(OUT_DIR, '%s__d%d.py' % (tid, s))
                with io.open(fn, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(code + '\n')
                rec['artifact'] = os.path.basename(fn)
                rec['code_lines'] = len(code.splitlines())
            u = r.get('usage') or {}
            tot_in += int(u.get('prompt_tokens') or 0)
            tot_out += int(u.get('completion_tokens') or 0)
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
            fh.flush()
            print('[qwen] %d %s d%d %s in=%s out=%s wall=%.1fs %s' % (
                n, tid, s, 'OK' if r.get('text') else 'FAIL',
                u.get('prompt_tokens'), u.get('completion_tokens'), rec['wall'],
                (r.get('err') or '')[:100]), flush=True)
    fh.close()
    print('[qwen] calls=%d tokens_in=%d tokens_out=%d out=%s' % (n, tot_in, tot_out, OUT_DIR), flush=True)


if __name__ == '__main__':
    main()
