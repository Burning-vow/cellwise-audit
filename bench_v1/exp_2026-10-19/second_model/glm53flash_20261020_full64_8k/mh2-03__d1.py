import argparse, json, random, heapq, math

def draw_service(rng, means, p):
    m = means[0] if rng.random() < p else means[1]
    return rng.expovariate(1.0 / m)

def run_seed(seed, lam, means, p, c, H, warm):
    rng = random.Random(seed)
    heap = []
    queue = []
    busy_count = 0
    next_arr = rng.expovariate(lam)
    t = 0.0
    last = 0.0
    area = 0.0
    busy_area = 0.0
    events = 0
    arr_win = 0
    wait_win = 0
    dep_t = []
    dep_w = []
    inf = float('inf')
    while True:
        next_dep = heap[0] if heap else inf
        t2 = min(next_arr, next_dep, H)
        n = busy_count + len(queue)
        area += n * (t2 - last)
        if n > 0:
            busy_area += (t2 - last)
        last = t2
        t = t2
        events += 1
        if t >= H:
            break
        if next_arr <= next_dep:
            waited = n >= c
            if t >= warm:
                arr_win += 1
                if waited:
                    wait_win += 1
            svc = draw_service(rng, means, p)
            if busy_count < c:
                busy_count += 1
                heapq.heappush(heap, t + svc)
            else:
                queue.append(t)
                queue.append(svc)
            next_arr = t + rng.expovariate(lam)
        else:
            heapq.heappop(heap)
            busy_count -= 1
            if queue:
                a0 = queue.pop(0)
                s0 = queue.pop(0)
                heapq.heappush(heap, t + s0)
                busy_count += 1
                if t >= warm:
                    dep_t.append(t - a0)
    win = H - warm
    ndep = len(dep_t)
    W = (sum(dep_t) / ndep) if ndep > 0 else 0.0
    L = area / win
    busy_frac = busy_area / win
    p_wait = (wait_win / arr_win) if arr_win > 0 else 0.0
    return L, W, busy_frac, p_wait, arr_win, ndep, events

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    args = ap.parse_args()
    nseeds = args.seeds
    H = float(args.horizon)
    S = int(args.seed_start)
    pert = args.pert
    lam = 3.0
    mbar = 6.0 / 60.0
    cv = 2.0
    p = 1.0 / (1.0 + cv * cv)
    m1 = (0.2 + math.sqrt(0.04 + 0.2)) / 2.0 * (mbar / 0.1)
    m1 = 0.345 * (mbar / 0.1)
    m2 = 0.03875 * (mbar / 0.1)
    means = [m1, m2]
    c = 1
    if pert == 'lam_up':
        lam *= 1.1
    elif pert == 'mu_up':
        means = [m / 1.1 for m in means]
    elif pert == 'c_up':
        c = 2
    warm = 0.25 * H
    win = H - warm
    seed_list = list(range(S, S + nseeds))
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    arrs = []
    deps = []
    evs = []
    for s in seed_list:
        L, W, bf, pw, a, d, e = run_seed(s, lam, means, p, c, H, warm)
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        arrs.append(a)
        deps.append(d)
        evs.append(e)
    n = len(seed_list)
    out = {
        'L': sum(per_L) / n,
        'W': sum(per_W) / n,
        'busy_frac': sum(per_bf) / n,
        'busy_util': sum(per_bf) / n,
        'busy_occupied': 1.0 - (1.0 - sum(per_bf) / n),
        'runtime_units': sum(evs) / n,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'hour',
        'win': win,
        'arr': sum(arrs) / n,
        'blk': 0.0,
        'dep': sum(deps) / n,
        'dep_rate': (sum(deps) / n) / win,
        'lam_eff': (sum(deps) / n) / win,
        'p_loss': 0.0,
        'p_wait': sum(per_pw) / n,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
