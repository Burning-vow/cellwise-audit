import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 3.0
    mu = 10.0
    cv = 1.5
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2
    mean_s = 1.0 / mu
    var_s = (cv * mean_s) ** 2
    p = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s * mean_s) / (var_s + mean_s * mean_s))))
    p = min(max(p, 0.01), 0.99)
    r1 = 1.0 / (2.0 * p * mean_s)
    r2 = 1.0 / (2.0 * (1.0 - p) * mean_s)
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        queue = []
        arr = dep = blk = 0
        area = busy_t = wait_area = 0.0
        wait_n = 0
        last = 0.0
        while True:
            rate = lam if n == 0 else lam
            dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                if busy:
                    endt = min(H, t + rem)
                    if t >= warm:
                        area += n * (endt - t)
                        busy_t += (endt - t)
                    rem -= (endt - t)
                    t = endt
                if t < H and t >= warm:
                    area += n * (H - t)
                break
            if t >= warm:
                area += n * (nt - t)
                if busy:
                    busy_t += (nt - t)
            t = nt
            if busy:
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    n -= 1
                    dep += 1
                    if queue:
                        cust = queue.pop(0)
                        if t >= warm:
                            wait_area += (t - cust[0])
                            wait_n += 1
                        busy = True
                        n += 1
                        rem = cust[1]
            arr += 1
            if rng.random() < p:
                st = rng.expovariate(r1)
            else:
                st = rng.expovariate(r2)
            if not busy:
                busy = True
                n += 1
                rem = st
            else:
                queue.append((t, st))
        win = H - warm
        tot_win += win
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy_t
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        Ls = area / win if win > 0 else 0.0
        Ws = (wait_area + busy_t) / dep if dep > 0 else 0.0
        bfs = busy_t / win if win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(0.0)
        per_pw.append(wait_n / arr if arr > 0 else 0.0)
    win = tot_win / len(seeds) if seeds else 0.0
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = (tot_wait_area + tot_busy) / tot_dep if tot_dep > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr_avg = tot_arr / len(seeds) if seeds else 0.0
    dep_avg = tot_dep / len(seeds) if seeds else 0.0
    blk_avg = tot_blk / len(seeds) if seeds else 0.0
    dep_rate = dep_avg / win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'win': win,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_loss': 0.0,
        'p_wait': (tot_wait_n / tot_arr) if tot_arr > 0 else 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
