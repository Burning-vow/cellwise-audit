import argparse, json, heapq, random, math

def run_seed(seed, horizon, warm, lam, mu, c):
    rng = random.Random(seed)
    t = 0.0
    servers = [math.inf] * c
    heapq.heapify(servers)
    queue = []
    ev = []
    heapq.heappush(ev, (rng.expovariate(lam), 'arr'))
    area_N = 0.0; area_min = 0.0; area_occ = 0.0
    arr_w = 0; dep_w = 0; wait_w = 0
    sL = 0.0; sW = 0.0; nW = 0
    last = 0.0
    while ev:
        te, kind = heapq.heappop(ev)
        if te > horizon: break
        area_N += (te - last) * (len(queue) + sum(1 for s in servers if s < math.inf))
        area_min += (te - last) * min(len(queue) + sum(1 for s in servers if s < math.inf), c)
        area_occ += (te - last) * (1 if any(s < math.inf for s in servers) or queue else 0)
        last = te
        t = te
        if kind == 'arr':
            st = rng.expovariate(mu)
            busy = sum(1 for s in servers if s < math.inf)
            if busy < c:
                heapq.heappush(servers, t + st)
            else:
                queue.append((t, st))
            if t >= warm:
                arr_w += 1
                if busy >= c: wait_w += 1
            heapq.heappush(ev, (t + rng.expovariate(lam), 'arr'))
        else:
            dep_w += 1 if t >= warm else 0
            if queue:
                at, st = queue.pop(0)
                heapq.heappush(servers, t + st)
                if t >= warm:
                    sL += (t - at) + st
                    nW += 1
            else:
                s = min(servers)
                if s < math.inf:
                    servers.remove(s)
                    heapq.heapify(servers)
    win = horizon - warm
    L = area_N / win
    busy_util = area_min / (c * win)
    p_wait = wait_w / arr_w if arr_w else 0.0
    W = (sL / nW) * 60.0 if nW else 0.0
    return L, W, busy_util, p_wait, arr_w, dep_w

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu, c = 8.0, 10.0, 2
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': c += 1
    horizon = a.horizon
    warm = 0.25 * horizon
    per = []
    seed_list = []
    for i in range(a.seeds):
        sd = a.seed_start + i
        seed_list.append(sd)
        per.append(run_seed(sd, horizon, warm, lam, mu, c))
    n = len(per)
    out = {
        'L': sum(p[0] for p in per) / n,
        'W': sum(p[1] for p in per) / n,
        'busy_frac': sum(p[2] for p in per) / n,
        'p_wait': sum(p[3] for p in per) / n,
        'runtime_units': 'minute',
        'time_unit': 'hour',
        'win': horizon - warm,
        'seed_list': seed_list,
        'seeds_used': n,
        'arr': sum(p[4] for p in per) / n,
        'dep': sum(p[5] for p in per) / n,
        'blk': 0.0,
        'busy_util': sum(p[2] for p in per) / n,
        'busy_occupied': sum(1 - (p[3] * 0 + p[2]) for p in per) / n,
        'dep_rate': (sum(p[5] for p in per) / n) / (horizon - warm),
        'lam_eff': (sum(p[4] for p in per) / n) / (horizon - warm),
        'p_loss': 0.0,
        'per_seed_L': [p[0] for p in per],
        'per_seed_W': [p[1] for p in per],
        'per_seed_busy_frac': [p[2] for p in per],
        'per_seed_p_loss': [0.0] * n,
        'per_seed_p_wait': [p[3] for p in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
