import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 9.0 / 60.0
    mu = 1.0 / 6.0
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        K = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy = 0.0
    tot_util = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        queue = []
        arr_w = 0
        dep_w = 0
        blk_w = 0
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        wait_sum = 0.0
        served_w = 0
        last = warm
        while True:
            rate = lam if n < K else 0.0
            if rate > 0:
                dt = rng.expovariate(rate)
                t_next = t + dt
            else:
                t_next = float('inf')
            if busy:
                st = queue[0][1]
                t_dep = st
            else:
                t_dep = float('inf')
            t_ev = min(t_next, t_dep)
            if t_ev > H:
                if t < H:
                    dt = H - t
                    if t >= warm:
                        area_n += n * dt
                        area_busy += (1 if busy else 0) * dt
                        area_util += min(n, 1) * dt
                    elif t + dt > warm:
                        dt2 = t + dt - warm
                        area_n += n * dt2
                        area_busy += (1 if busy else 0) * dt2
                        area_util += min(n, 1) * dt2
                break
            if t_ev > warm:
                dt = t_ev - max(t, warm)
                area_n += n * dt
                area_busy += (1 if busy else 0) * dt
                area_util += min(n, 1) * dt
            t = t_ev
            if t_next <= t_dep:
                if n < K:
                    n += 1
                    if t >= warm:
                        arr_w += 1
                    svc = rng.expovariate(mu)
                    if not busy:
                        busy = True
                        queue.append((t, t + svc))
                    else:
                        queue.append((t, t + svc))
                else:
                    if t >= warm:
                        blk_w += 1
            else:
                queue.pop(0)
                n -= 1
                if t >= warm:
                    dep_w += 1
                    served_w += 1
                    wait_sum += 0.0
                if queue:
                    queue[0] = (queue[0][0], t + (queue[0][1] - queue[0][0]))
                else:
                    busy = False
        win = H - warm
        Ls = area_n / win
        bf = area_busy / win
        ut = area_util / win
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = 0.0
        per_L.append(Ls)
        per_W.append(Ls / (dep_w / win) if dep_w > 0 else 0.0)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_busy += bf
        tot_util += ut
        tot_served += served_w
    ns = len(seeds)
    win = H - warm
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    busy_frac = tot_busy / ns
    p_loss = sum(per_pl) / ns
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / win
    busy_util = tot_util / ns
    lam_eff = arr_avg / win
    p_wait = 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_util,
        'busy_occupied': busy_frac,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
