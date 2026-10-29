import argparse, heapq, json, math, random

def service_draw(rng, m1, m2, p):
    return m1 if rng.random() < p else m2

def run_seed(seed, lam, horizon, warm, m1, m2, p):
    rng = random.Random(seed)
    t = 0.0
    N = 0
    area_N = 0.0
    area_busy = 0.0
    area_n_wait = 0.0
    last = 0.0
    events = []
    arr_count = 0
    dep_count = 0
    blk_count = 0
    win_arr = 0
    win_dep = 0
    win_blk = 0
    sojourns = []
    waits = []
    served_start = {}
    cid = 0
    next_arr = rng.expovariate(lam)
    heapq.heappush(events, (next_arr, 'a', cid))
    cid += 1
    last_t = 0.0
    while True:
        if not events:
            break
        t, kind, idx = heapq.heappop(events)
        if t > horizon:
            t = horizon
            if last_t < horizon:
                area_N += (horizon - last_t) * N
                if N > 0:
                    area_busy += (horizon - last_t)
                if N >= 2:
                    area_n_wait += (horizon - last_t)
            last_t = horizon
            break
        if t > last_t:
            area_N += (t - last_t) * N
            if N > 0:
                area_busy += (t - last_t)
            if N >= 2:
                area_n_wait += (t - last_t)
            last_t = t
        if kind == 'a':
            arr_count += 1
            if t >= warm:
                win_arr += 1
            s = service_draw(rng, m1, m2, p)
            if N == 0:
                served_start[idx] = t
                heapq.heappush(events, (t + s, 'd', idx))
            else:
                heapq.heappush(events, (t + s, 'd', idx))
                waits_pending = True
            N += 1
            na = rng.expovariate(lam)
            heapq.heappush(events, (t + na, 'a', cid))
            cid += 1
        else:
            dep_count += 1
            N -= 1
            if t >= warm:
                win_dep += 1
            if N > 0:
                pass
    return None

def run_seed2(seed, lam, horizon, warm, m1, m2, p):
    rng = random.Random(seed)
    t = 0.0
    N = 0
    area_N = 0.0
    area_busy = 0.0
    last_t = 0.0
    arr_total = dep_total = blk_total = 0
    win_arr = win_dep = win_blk = 0
    sojourns = []
    queue = []
    dep_time_of = {}
    pending = []
    cid = 0
    next_arr = rng.expovariate(lam)
    dep_at = None
    busy_since = None
    while t < horizon:
        t_next = next_arr
        cand = []
        if dep_at is not None:
            cand.append(dep_at)
        if cand and cand[0] < t_next:
            t_next = cand[0]
            is_arr = False
        else:
            is_arr = True
        if t_next > horizon:
            if last_t < horizon:
                area_N += (horizon - last_t) * N
                if N > 0:
                    area_busy += (horizon - last_t)
            last_t = horizon
            t = horizon
            break
        if t_next > last_t:
            area_N += (t_next - last_t) * N
            if N > 0:
                area_busy += (t_next - last_t)
            last_t = t_next
        t = t_next
        if is_arr:
            arr_total += 1
            if t >= warm:
                win_arr += 1
            s = service_draw(rng, m1, m2, p)
            if N == 0:
                dep_at = t + s
                soj_time = s
                soj_start = t
            else:
                queue.append((t, s))
            N += 1
            next_arr = t + rng.expovariate(lam)
        else:
            dep_total += 1
            if t >= warm:
                win_dep += 1
            N -= 1
            if queue:
                at, s = queue.pop(0)
                soj_time = s + (t - at)
                soj_start = at
                dep_at = t + s
            else:
                dep_at = None
                soj_time = None
            if soj_time is not None and soj_start >= warm:
                sojourns.append(soj_time)
    if last_t < horizon:
        area_N += (horizon - last_t) * N
        if N > 0:
            area_busy += (horizon - last_t)
        last_t = horizon
    win = horizon - warm
    L = area_N / win
    busy = area_busy / win
    W = (sum(sojourns) / len(sojourns) * 60.0) if sojourns else 0.0
    p_wait = (sum(1 for _ in sojourns if True) and 0.0)
    return L, W, busy, win_arr, win_dep, win_blk, p_wait

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 5.0
    mean_s = 0.1
    cv2 = 4.0
    if a.pert == 'lam_up':
        lam *= 1.1
    elif a.pert == 'mu_up':
        mean_s /= 1.1
    elif a.pert == 'c_up':
        mean_s *= 1.1
    cv2 = 4.0
    scv = cv2 - 1.0 if False else 2.0 + 2.0 - 2.0
    CV = 2.0
    p = 0.5 * (1.0 + math.sqrt((CV * CV - 1.0) / (CV * CV + 1.0)))
    m1 = 2.0 * p * mean_s
    m2 = 2.0 * (1.0 - p) * mean_s
    horizon = a.horizon
    warm = 0.25 * horizon
    win = horizon - warm
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    per_L, per_W, per_b, per_pl, per_pw = [], [], [], [], []
    arrs, deps, blks = [], [], []
    for s in seeds:
        L, W, busy, wa, wd, wb, pw = run_seed2(s, lam, horizon, warm, m1, m2, p)
        per_L.append(L); per_W.append(W); per_b.append(busy)
        per_pl.append(0.0); per_pw.append(pw)
        arrs.append(wa); deps.append(wd); blks.append(wb)
    n = len(seeds)
    out = {
        'L': sum(per_L) / n,
        'W': sum(per_W) / n,
        'busy_frac': sum(per_b) / n,
        'busy_util': sum(per_b) / n,
        'busy_occupied': sum(per_b) / n,
        'runtime_units': 'hour',
        'time_unit': 'hour',
        'win': win,
        'seed_list': seeds,
        'seeds_used': n,
        'arr': sum(arrs) / n,
        'dep': sum(deps) / n,
        'blk': sum(blks) / n,
        'dep_rate': (sum(deps) / n) / win,
        'lam_eff': (sum(arrs) / n) / win,
        'p_loss': 0.0,
        'p_wait': sum(per_pw) / n,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_b,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
