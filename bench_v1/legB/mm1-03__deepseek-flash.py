import json, random, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=8)
    p.add_argument('--horizon', type=float, default=2000.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()

    lam = 6.0
    mu = 10.0
    c = 1.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c *= 1.2

    seeds = [a.seed_start + i for i in range(a.seeds)]
    H = a.horizon
    warm = 0.25 * H

    per_L = []
    per_W = []
    per_busy = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_dep_rate = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0.0
        area_n = 0.0
        area_busy = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        sum_sojourn = 0.0
        n_dep = 0
        queue = []
        server_free_at = 0.0
        next_arr = rng.expovariate(lam)
        last_t = 0.0
        win_start = warm
        win_len = H - warm

        while t < H:
            if next_arr <= server_free_at and next_arr <= H:
                nt = next_arr
            elif server_free_at <= H:
                nt = server_free_at
            else:
                nt = H
            if nt > H:
                nt = H
            dt = nt - t
            if t >= win_start:
                area_n += n * dt
                area_busy += (1 if n > 0 else 0) * dt
            t = nt
            if t >= H:
                break
            if abs(t - next_arr) < 1e-12:
                svc = rng.expovariate(mu) / c
                queue.append((t, svc))
                n += 1
                if t >= win_start:
                    arr_w += 1
                next_arr = t + rng.expovariate(lam)
                if n == 1:
                    server_free_at = t + svc
            elif abs(t - server_free_at) < 1e-12:
                if queue:
                    at, svc = queue.pop(0)
                    soj = t - at
                    if t >= win_start:
                        dep_w += 1
                        sum_sojourn += soj
                        n_dep += 1
                    n -= 1
                    if n > 0:
                        nat, nsvc = queue[0]
                        server_free_at = t + nsvc
                    else:
                        server_free_at = float('inf')
                else:
                    server_free_at = float('inf')

        if win_len > 0:
            L_est = area_n / win_len
            busy_frac = area_busy / win_len
        else:
            L_est = 0.0
            busy_frac = 0.0
        W_est = (sum_sojourn / n_dep) if n_dep > 0 else 0.0
        per_L.append(L_est)
        per_W.append(W_est)
        per_busy.append(busy_frac)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += (arr_w - dep_w)
        tot_dep_rate += (dep_w / win_len) if win_len > 0 else 0.0
        win_total += win_len

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = tot_dep_rate / ns
    win = win_total / ns

    out = {
        "L": L,
        "W": W,
        "arr": arr,
        "blk": blk,
        "dep": dep,
        "dep_rate": dep_rate,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy,
        "runtime_units": "simulation",
        "seed_list": seeds,
        "seeds_used": ns,
        "time_unit": "minute",
        "win": win
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
