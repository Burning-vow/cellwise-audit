import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    c = 2
    if a.pert == 'lam_up': lam *= 1.25
    elif a.pert == 'mu_up': mu *= 1.25
    elif a.pert == 'c_up': c = 3
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_soj = 0.0
    tot_dep_t = 0.0
    win_total = 0.0
    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = [None] * c
        areaN = 0.0; areaB = 0.0
        wait_sum = 0.0; soj_sum = 0.0
        arr_w = 0; dep_w = 0; blk_w = 0
        dep_t_w = 0.0
        last = 0.0
        while True:
            rate = lam + busy * mu
            if rate <= 0:
                dt = float('inf')
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                if t < H:
                    areaN += n * (H - t)
                    areaB += busy * (H - t)
                break
            if t >= warm:
                areaN += n * (nt - t)
                areaB += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                svc = rng.expovariate(mu)
                if t >= warm: arr_w += 1
                if busy < c:
                    busy += 1
                    servers[busy - 1] = (t + svc, t, svc)
                    if t >= warm:
                        wait_sum += 0.0
                        soj_sum += svc
                else:
                    queue.append((t, svc))
            else:
                idx = -1
                for i in range(c):
                    if servers[i] is not None and servers[i][0] <= t + 1e-12:
                        idx = i; break
                if idx < 0:
                    idx = 0
                    for i in range(c):
                        if servers[i] is not None and servers[i][0] < servers[idx][0]:
                            idx = i
                end, at, svc = servers[idx]
                if t >= warm:
                    dep_w += 1
                    dep_t_w += t
                if queue:
                    at2, svc2 = queue.pop(0)
                    if t >= warm:
                        wait_sum += (t - at2)
                        soj_sum += (t - at2) + svc2
                    servers[idx] = (t + svc2, at2, svc2)
                else:
                    busy -= 1
                    servers[idx] = None
        win = H - warm
        win_total += win
        L = areaN / win if win > 0 else 0.0
        bf = areaB / (c * win) if win > 0 else 0.0
        W = (wait_sum + soj_sum) / dep_w if dep_w > 0 else 0.0
        pw = 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf)
        per_pl.append(0.0); per_pw.append(pw)
        tot_arr += arr_w; tot_dep += dep_w; tot_blk += blk_w
        tot_areaN += areaN; tot_areaB += areaB
        tot_wait += wait_sum; tot_soj += soj_sum
        tot_dep_t += dep_t_w
    n_seeds = a.seeds
    win = win_total / n_seeds if n_seeds > 0 else 0.0
    L = tot_areaN / (n_seeds * win) if win > 0 else 0.0
    busy_frac = tot_areaB / (c * n_seeds * win) if win > 0 else 0.0
    W = (tot_wait + tot_soj) / tot_dep if tot_dep > 0 else 0.0
    arr = tot_arr / n_seeds
    dep = tot_dep / n_seeds
    blk = tot_blk / n_seeds
    dep_rate = (tot_dep / n_seeds) / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    p_loss = blk / arr if arr > 0 else 0.0
    p_wait = sum(per_pw) / n_seeds if n_seeds > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': H, 'seed_list': [a.seed_start + i for i in range(n_seeds)],
        'seeds_used': n_seeds, 'time_unit': 'minute', 'win': win,
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': p_loss,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
