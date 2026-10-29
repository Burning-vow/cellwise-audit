import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 10.0
    c = 1
    if a.pert == 'lam_up':
        lam = 7.2
    elif a.pert == 'mu_up':
        mu = 12.0
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    svc = 60.0 / mu

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_waiters = 0.0
    tot_served = 0.0
    win_total = 0.0
    seeds = []

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seeds.append(s)
        t = 0.0
        n = 0
        busy = 0
        free = [0.0] * c
        queue = []
        area = 0.0
        busy_area = 0.0
        arr = 0
        dep = 0
        blk = 0
        wait_sum = 0.0
        wait_cnt = 0
        served = 0
        last = 0.0
        while True:
            rate = lam / 60.0
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                break
            area += n * (nt - t)
            busy_area += busy * (nt - t)
            t = nt
            arr += 1
            if busy < c:
                busy += 1
                free[busy - 1] = t + svc
                if t >= warm:
                    wait_cnt += 1
                    served += 1
            else:
                queue.append(t)
            while busy > 0 and free[busy - 1] <= t:
                busy -= 1
                if queue:
                    at = queue.pop(0)
                    w = t - at
                    if t >= warm:
                        wait_sum += w
                        wait_cnt += 1
                        served += 1
                    busy += 1
                    free[busy - 1] = t + svc
        area += n * (H - t)
        busy_area += busy * (H - t)
        win = H - warm
        Ls = area / H
        Ws = Ls / (lam / 60.0)
        bfs = busy_area / H
        pls = blk / arr if arr > 0 else 0.0
        pws = wait_cnt / served if served > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_area += area
        tot_busy += busy_area
        tot_wait += wait_sum
        tot_waiters += wait_cnt
        tot_served += served
        win_total += win

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    busy_frac = sum(per_bf) / ns
    p_loss = sum(per_pl) / ns
    p_wait = sum(per_pw) / ns
    arr_avg = tot_arr / ns
    dep_avg = tot_dep / ns
    blk_avg = tot_blk / ns
    dep_rate = dep_avg / (win_total / ns) * 60.0 if win_total > 0 else 0.0
    lam_eff = lam * (1.0 - p_loss)

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win_total / ns,
        'arr': arr_avg,
        'blk': blk_avg,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
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
