import argparse, json, heapq, random

def run_seed(seed, lam, mu, c, horizon):
    rng = random.Random(seed)
    warm = horizon * 0.25
    ev = []
    seq = 0
    def push(t, kind, data):
        nonlocal seq
        heapq.heappush(ev, (t, seq, kind, data)); seq += 1
    push(rng.expovariate(lam), 'arr', None)
    t = 0.0; n = 0; queue = []
    area_n = 0.0; area_min = 0.0; area_occ = 0.0
    last = 0.0
    arr_w = 0; dep_w = 0; wait_w = 0; soj_sum = 0.0; soj_cnt = 0
    def integrate(tnew):
        nonlocal area_n, area_min, area_occ, last
        if tnew > last:
            dt = tnew - last
            if tnew > warm:
                a = max(last, warm)
                d = tnew - a
                if d > 0:
                    area_n += n * d
                    area_min += min(n, c) * d
                    if n > 0: area_occ += d
            last = tnew
    while ev:
        t, _, kind, data = heapq.heappop(ev)
        if t > horizon: break
        integrate(t)
        if kind == 'arr':
            svc = rng.expovariate(mu)
            if t >= warm: arr_w += 1
            waited = n >= c
            if t >= warm and waited: wait_w += 1
            n += 1
            if n <= c:
                push(t + svc, 'dep', (t, svc))
            else:
                queue.append((t, svc))
            push(t + rng.expovariate(lam), 'arr', None)
        else:
            arr_t, svc = data
            n -= 1
            dep_w = dep_w + (1 if arr_t >= warm else 0)
            if arr_t >= warm:
                soj_sum += (t - arr_t); soj_cnt += 1
            if queue:
                a2, s2 = queue.pop(0)
                push(t + s2, 'dep', (a2, s2))
    win = horizon - warm
    L = area_n / win
    W = (soj_sum / soj_cnt) * 60.0 if soj_cnt else 0.0
    busy = area_min / win / c
    p_wait = wait_w / arr_w if arr_w else 0.0
    occ = area_occ / win
    return {'L': L, 'W': W, 'busy_frac': busy, 'busy_util': busy,
            'busy_occupied': occ, 'p_wait': p_wait, 'arr': arr_w, 'dep': dep_w,
            'blk': 0, 'dep_rate': dep_w / win, 'lam_eff': arr_w / win,
            'p_loss': 0.0}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu, c = 8.0, 6.0, 2
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': c = 3
    per = []
    seed_list = []
    for k in range(a.seeds):
        s = a.seed_start + k
        seed_list.append(s)
        per.append(run_seed(s, lam, mu, c, a.horizon))
    m = len(per)
    def avg(key): return sum(p[key] for p in per) / m
    out = {
        'L': avg('L'), 'W': avg('W'), 'busy_frac': avg('busy_frac'),
        'busy_util': avg('busy_util'), 'busy_occupied': avg('busy_occupied'),
        'p_wait': avg('p_wait'), 'arr': avg('arr'), 'dep': avg('dep'),
        'blk': avg('blk'), 'dep_rate': avg('dep_rate'), 'lam_eff': avg('lam_eff'),
        'p_loss': avg('p_loss'), 'runtime_units': 1, 'time_unit': 'hour',
        'win': a.horizon * 0.75, 'seed_list': seed_list, 'seeds_used': m,
        'per_seed_L': [p['L'] for p in per], 'per_seed_W': [p['W'] for p in per],
        'per_seed_busy_frac': [p['busy_frac'] for p in per],
        'per_seed_p_loss': [p['p_loss'] for p in per],
        'per_seed_p_wait': [p['p_wait'] for p in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
