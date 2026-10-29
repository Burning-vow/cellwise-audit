import argparse, json, heapq, math, random

def run(seed, lam, mu, horizon, warm):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    area = 0.0
    busy_area = 0.0
    wait_sum = 0.0
    wait_cnt = 0
    served = 0
    arrivals = 0
    last = t
    svc = {}
    def schedule(k, s):
        svc[k] = s
    events = []
    heapq.heappush(events, (rng.expovariate(lam), 'a', 0))
    next_id = 0
    waiters = []
    while True:
        if not events:
            break
        t2, kind, arg = heapq.heappop(events)
        if t2 > horizon:
            break
        dt = t2 - t
        if t2 > warm:
            area += n * dt
            busy_area += (1 if n >= 1 else 0) * dt
        t = t2
        if kind == 'a':
            next_id += 1
            arrivals += 1
            s = rng.expovariate(mu)
            if n == 0:
                heapq.heappush(events, (t + s, 'd', next_id))
                schedule(next_id, s)
                if t >= warm:
                    wait_sum += 0.0
                    wait_cnt += 1
                    served += 1
            else:
                if t >= warm:
                    wait_cnt += 1
                waiters.append((t, s))
                schedule(next_id, s)
            heapq.heappush(events, (t + rng.expovariate(lam), 'a', 0))
        else:
            n -= 1
            if t >= warm:
                served += 1
            if waiters:
                at, s = waiters.pop(0)
                if t >= warm:
                    wait_sum += t - at
                heapq.heappush(events, (t + s, 'd', arg))
        if kind == 'a':
            n += 1
    win = horizon - warm
    p0 = 1 - busy_area / win if win > 0 else 0.0
    return area / win if win > 0 else 0.0, (wait_sum / wait_cnt * 60 if wait_cnt else 0.0), busy_area / win, wait_cnt / arrivals if arrivals else 0.0, arrivals, served, p0, win

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu_h, c = 7.0, 10.0, 1.0
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu_h *= 1.1
    elif a.pert == 'c_up': c = 2.0
    warm = a.horizon * 0.25
    seeds = [a.seed_start + i for i in range(a.seeds)]
    Ls, Ws, bfs, pws, pls = [], [], [], [], []
    ta, td = 0.0, 0.0
    for s in seeds:
        L, W, bf, pw, arr, dep, p0, win = run(s, lam, mu_h, a.horizon, warm)
        Ls.append(L); Ws.append(W); bfs.append(bf); pws.append(pw); pls.append(0.0)
        ta += arr / a.seeds; td += dep / a.seeds
    n = len(seeds)
    Lm = sum(Ls) / n; Wm = sum(Ws) / n; bfm = sum(bfs) / n; pwm = sum(pws) / n
    out = {
        "L": Lm, "W": Wm, "busy_frac": bfm, "p_wait": pwm,
        "runtime_units": a.horizon, "seed_list": seeds, "seeds_used": n,
        "time_unit": "hour", "win": a.horizon * 0.75,
        "arr": ta, "blk": 0.0, "busy_util": bfm, "busy_occupied": bfm,
        "dep": td, "dep_rate": td / (a.horizon * 0.75), "lam_eff": ta / (a.horizon * 0.75),
        "p_loss": 0.0,
        "per_seed_L": Ls, "per_seed_W": Ws, "per_seed_busy_frac": bfs,
        "per_seed_p_loss": pls, "per_seed_p_wait": pws
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
