import argparse, json, random, heapq, math

def run_seed(seed, lam, horizon, warm):
    rng = random.Random(seed)
    t = 0.0
    arrivals = []
    while t < horizon:
        t += rng.expovariate(lam)
        if t < horizon:
            arrivals.append(t)
    events = []
    for a in arrivals:
        events.append((a, 0, None))
    n = len(arrivals)
    heapq.heapify(events)
    busy_until = None
    queue = []
    in_service = None
    area_N = 0.0
    area_B = 0.0
    last = 0.0
    waits = []
    sojourns = []
    dep = 0
    arr_cnt = 0
    wait_cnt = 0
    served_arr = []
    served_soj = []
    served_wait = []
    serv_start = {}
    processed = set()

    def integrate(now):
        nonlocal area_N, area_B, last
        dt = now - last
        if dt > 0:
            b = 1.0 if (in_service is not None or (queue)) else 0.0
            if now > warm:
                if last >= warm:
                    area_N += n_now * dt
                    area_B += b * dt
                else:
                    f = (now - warm) / dt
                    area_N += n_now * dt * f
                    area_B += b * dt * f
        last = now

    n_now = 0
    eid = 0
    while events:
        t, kind, cust = heapq.heappop(events)
        integrate(t)
        if kind == 0:
            n_now += 1
            arr_cnt += 1
            served = (cust, t)
            if in_service is None:
                in_service = cust
                heapq.heappush(events, (t + SERVICE, 1, cust))
            else:
                queue.append((cust, t))
        elif kind == 1:
            n_now -= 1
            dep += 1
            in_service = None
            if queue:
                nc, nt = queue.pop(0)
                in_service = nc
                heapq.heappush(events, (t + SERVICE, 1, nc))
        if t > warm:
            pass
    return None

SERVICE = 5.0 / 60.0

def sim(seed, lam, horizon, warm):
    rng = random.Random(seed)
    t = 0.0
    arrs = []
    while True:
        t += rng.expovariate(lam)
        if t >= horizon:
            break
        arrs.append((t, SERVICE))
    next_free = float('inf')
    start_times = []
    cur = -1.0
    aN = 0.0
    aB = 0.0
    last = 0.0
    lev = 0
    dep_t = []
    evs = sorted(arrs)
    # simple FCFS single server, deterministic service
    start = []
    prev_end = None
    i = 0
    ready = []
    events = []
    for idx, (a, s) in enumerate(arrs):
        events.append((a, 0, idx, s))
    import heapq as hq
    hq.heapify(events)
    q = []
    busy_end = None
    in_srv = None
    N = 0
    stats = {'aN': 0.0, 'aB': 0.0, 'last': 0.0}
    arr_w = 0; dep_w = 0; wait_w = 0; soj = []; waits = []

    def integ(now, N):
        dt = now - stats['last']
        if dt > 0 and now > warm:
            b = 1 if N > 0 else 0
            f = min(1.0, (now - warm) / dt)
            stats['aN'] += N * dt * f
            stats['aB'] += b * dt * f
        stats['last'] = now

    while events:
        t, k, idx, s = hq.heappop(events)
        integ(t, N)
        if k == 0:
            N += 1
            if t > warm:
                arr_w += 1
            if in_srv is None:
                in_srv = idx
                a = t
                hq.heappush(events, (t + s, 1, idx, s))
                if t > warm:
                    waits.append(0.0)
            else:
                q.append((idx, t))
        else:
            N -= 1
            if t > warm:
                dep_w += 1
                at = arr_time[idx]
                soj.append(t - at)
            in_srv = None
            if q:
                j, at = q.pop(0)
                in_srv = j
                hq.heappush(events, (t + s, 1, j, s))
                if t > warm:
                    waits.append(t - at)
    L = stats['aN'] / (horizon - warm)
    B = stats['aB'] / (horizon - warm)
    W = (sum(soj) / len(soj)) if soj else 0.0
    pw = (sum(1 for w in waits if w > 1e-12) / len(waits)) if waits else 0.0
    return L, W, B, arr_w, dep_w, pw, len(waits)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=2000.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    lam = 8.0
    mu = 1.0 / SERVICE
    c = 1.0
    if a.pert == 'lam_up':
        lam *= 1.1
    elif a.pert == 'mu_up':
        mu *= 1.1
    elif a.pert == 'c_up':
        c += 1
    serv = 1.0 / mu
    global SERVICE
    SERVICE = serv
    warm = a.horizon * 0.25
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    per_L, per_W, per_B, per_pl, per_pw = [], [], [], [], []
    arrs_, deps_ = [], []
    for s in seeds:
        L, W, B, aw, dw, pw, ns = sim(s, lam, a.horizon, warm)
        per_L.append(L); per_W.append(W); per_B.append(B)
        per_pl.append(0.0); per_pw.append(pw)
        arrs_.append(aw); deps_.append(dw)
    n = len(seeds)
    out = {
        'L': sum(per_L)/n, 'W': sum(per_W)/n,
        'busy_frac': sum(per_B)/n,
        'busy_util': sum(per_B)/n, 'busy_occupied': sum(per_B)/n,
        'runtime_units': a.horizon, 'seed_list': seeds, 'seeds_used': n,
        'time_unit': 'hour', 'win': a.horizon - warm,
        'arr': sum(arrs_)/n, 'dep': sum(deps_)/n, 'blk': 0.0,
        'dep_rate': (sum(deps_)/n) / (a.horizon - warm),
        'lam_eff': (sum(deps_)/n) / (a.horizon - warm),
        'p_loss': 0.0, 'p_wait': sum(per_pw)/n,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_B, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
