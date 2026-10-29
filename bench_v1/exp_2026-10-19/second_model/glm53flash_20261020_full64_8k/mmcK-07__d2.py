import argparse, json, heapq, random

def run_seed(seed, lam, mu, c, K, H):
    rng = random.Random(seed)
    T0 = 0.25 * H
    t = rng.expovariate(lam)
    heap = [(t, 0, 'a', None)]
    seq = 1
    lane_free = [0.0] * c
    N = 0
    prev = 0.0
    areaN = areaB = areaU = 0.0
    arr = blk = dep = 0
    waitn = waited_arr = 0
    soj = 0.0
    while heap and heap[0][0] < H:
        tt, _, typ, at = heapq.heappop(heap)
        if tt >= H:
            break
        if tt > T0:
            a = max(prev, T0)
            areaN += N * (tt - a)
            areaB += (1 if N > 0 else 0) * (tt - a)
            areaU += min(N, c) * (tt - a)
        prev = tt
        if typ == 'a':
            inwin = tt >= T0
            if inwin:
                arr += 1
            if N < K:
                N += 1
                s = rng.expovariate(mu)
                start = max(tt, min(lane_free))
                idx = lane_free.index(min(lane_free))
                lane_free[idx] = start + s
                if inwin:
                    waited_arr += 1
                    if start > tt:
                        waitn += 1
                heapq.heappush(heap, (start + s, seq, 'd', tt)); seq += 1
            else:
                if inwin:
                    blk += 1
            heapq.heappush(heap, (tt + rng.expovariate(lam), seq, 'a', None)); seq += 1
        else:
            N -= 1
            if tt >= T0:
                dep += 1
                soj += tt - at
    if H > T0:
        a = max(prev, T0)
        areaN += N * (H - a)
        areaB += (1 if N > 0 else 0) * (H - a)
        areaU += min(N, c) * (H - a)
    win = H - T0
    return {
        'win': win, 'L': areaN / win, 'W': (soj / dep) if dep else 0.0,
        'busy_frac': areaB / win, 'busy_occupied': areaB / win,
        'busy_util': areaU / (c * win),
        'p_loss': (blk / arr) if arr else 0.0,
        'p_wait': (waitn / waited_arr) if waited_arr else 0.0,
        'arr': arr, 'blk': blk, 'dep': dep,
        'dep_rate': dep / win, 'lam_eff': (arr - blk) / win,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu, c = 8.0, 5.0, 3
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.1
    elif a.pert == 'mu_up':
        mu *= 1.1
    elif a.pert == 'c_up':
        c = 4
    per = []
    seed_list = []
    for i in range(a.seeds):
        s = a.seed_start + i
        seed_list.append(s)
        per.append(run_seed(s, lam, mu, c, K, a.horizon))
    n = len(per)
    avg = lambda k: sum(p[k] for p in per) / n
    out = {
        'L': avg('L'), 'W': avg('W'), 'busy_frac': avg('busy_frac'),
        'p_loss': avg('p_loss'), 'p_wait': avg('p_wait'),
        'runtime_units': a.horizon, 'seed_list': seed_list,
        'seeds_used': n, 'time_unit': 'hour', 'win': per[0]['win'],
        'arr': avg('arr'), 'blk': avg('blk'), 'dep': avg('dep'),
        'dep_rate': avg('dep_rate'), 'lam_eff': avg('lam_eff'),
        'busy_util': avg('busy_util'), 'busy_occupied': avg('busy_occupied'),
        'per_seed_L': [p['L'] for p in per],
        'per_seed_W': [p['W'] for p in per],
        'per_seed_busy_frac': [p['busy_frac'] for p in per],
        'per_seed_p_loss': [p['p_loss'] for p in per],
        'per_seed_p_wait': [p['p_wait'] for p in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
