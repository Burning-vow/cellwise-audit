import argparse, json, heapq, math, random

def run_seed(seed, horizon, lam, mu):
    rng = random.Random(seed)
    warm = horizon * 0.25
    t = 0.0
    n = 0
    events = []
    heapq.heappush(events, (rng.expovariate(lam), 'a', 0.0, rng.expovariate(mu)))
    last = 0.0
    area_n = 0.0
    area_busy = 0.0
    waits = 0.0
    n_dep = 0
    n_wait = 0
    n_arr = 0
    n_loss = 0
    served = 0
    while events:
        et, kind, ta, sv = heapq.heappop(events)
        if et > horizon:
            break
        if et >= warm:
            area_n += n * (et - last)
            area_busy += (1 if n >= 1 else 0) * (et - last)
        last = et
        if kind == 'a':
            n_arr += 1
            nt = et + rng.expovariate(lam)
            if nt <= horizon:
                heapq.heappush(events, (nt, 'a', nt, rng.expovariate(mu)))
            if n == 0:
                n = 1
                heapq.heappush(events, (et + sv, 'd', ta, sv))
            else:
                n += 1
                heapq.heappush(events, (float('inf'), 'q', ta, sv))
        else:
            waits += et - ta
            served += 1
            if et - ta > 0:
                n_wait += 1
            if et >= warm:
                n_dep += 1
            n -= 1
            if n > 0:
                qt, qta, qsv = min((e for e in events if e[1] == 'q'), key=lambda e: e[0]) if False else (None, None, None)
                best = None
                for e in events:
                    if e[1] == 'q' and (best is None or e[0] < best[0]):
                        best = e
                heapq.heappush(events, (et + best[3], 'd', best[2], best[3]))
                events.remove(best)
    win = horizon - warm
    if win <= 0:
        win = 1e-9
    L = area_n / win
    busy = area_busy / win
    W = (waits / served) * 60.0 if served > 0 else 0.0
    pw = n_wait / served if served > 0 else 0.0
    return L, W, busy, pw, n_arr, n_dep, n_loss

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=10000)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu, c = 6.0, 10.0, 1
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': c += 1
    per_L, per_W, per_b, per_pl, per_pw = [], [], [], [], []
    seed_list = []
    tot_arr = tot_dep = tot_loss = 0.0
    win = a.horizon - a.horizon * 0.25
    for i in range(a.seeds):
        s = a.seed_start + i
        L, W, b, pw, arr, dep, loss = run_seed(s, a.horizon, lam, mu)
        seed_list.append(s)
        per_L.append(L); per_W.append(W); per_b.append(b)
        per_pl.append(loss); per_pw.append(pw)
        tot_arr += arr; tot_dep += dep; tot_loss += loss
    k = a.seeds
    L = sum(per_L) / k
    W = sum(per_W) / k
    busy_frac = sum(per_b) / k
    p_wait = sum(per_pw) / k
    p_loss = sum(per_pl) / k
    out = {
        "L": L, "W": W, "busy_frac": busy_frac, "p_wait": p_wait,
        "runtime_units": a.horizon, "seed_list": seed_list, "seeds_used": k,
        "time_unit": "hour", "win": win,
        "arr": tot_arr / k, "blk": tot_loss / k,
        "busy_util": busy_frac, "busy_occupied": busy_frac,
        "dep": tot_dep / k, "dep_rate": tot_dep / k / win,
        "lam_eff": tot_arr / k / win, "p_loss": p_loss,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_b, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
