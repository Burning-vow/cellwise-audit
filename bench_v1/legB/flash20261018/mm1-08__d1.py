import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 5.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        pass
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_busy = []
    per_ploss = []
    per_pwait = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy_area = 0.0
    tot_wait_area = 0.0
    tot_waiters_area = 0.0
    tot_served = 0.0
    tot_wait_count = 0.0
    win_total = 0.0
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        seeds.append(s)
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        waiters_area = 0.0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        served = 0
        wait_count = 0
        last = 0.0
        while True:
            if n == 0:
                dt = rng.expovariate(lam)
                t_next = t + dt
                if t_next > H:
                    if t < H:
                        area += n * (H - t)
                        busy_area += (1 if busy else 0) * (H - t)
                        waiters_area += max(n - 1, 0) * (H - t)
                    break
                if t >= warm:
                    area += n * (t_next - t)
                    busy_area += (1 if busy else 0) * (t_next - t)
                    waiters_area += max(n - 1, 0) * (t_next - t)
                t = t_next
                n += 1
                if t >= warm:
                    arr_c += 1
                svc = rng.expovariate(mu)
                if n == 1:
                    busy = True
                    next_dep = t + svc
                continue
            dt_arr = rng.expovariate(lam)
            t_arr = t + dt_arr
            t_dep = next_dep
            if t_arr < t_dep:
                if t_arr > H:
                    if t < H:
                        area += n * (H - t)
                        busy_area += (1 if busy else 0) * (H - t)
                        waiters_area += max(n - 1, 0) * (H - t)
                    break
                if t >= warm:
                    area += n * (t_arr - t)
                    busy_area += (1 if busy else 0) * (t_arr - t)
                    waiters_area += max(n - 1, 0) * (t_arr - t)
                t = t_arr
                n += 1
                if t >= warm:
                    arr_c += 1
                svc = rng.expovariate(mu)
                if n == 1:
                    busy = True
                    next_dep = t + svc
            else:
                if t_dep > H:
                    if t < H:
                        area += n * (H - t)
                        busy_area += (1 if busy else 0) * (H - t)
                        waiters_area += max(n - 1, 0) * (H - t)
                    break
                if t >= warm:
                    area += n * (t_dep - t)
                    busy_area += (1 if busy else 0) * (t_dep - t)
                    waiters_area += max(n - 1, 0) * (t_dep - t)
                t = t_dep
                n -= 1
                if t >= warm:
                    dep_c += 1
                    served += 1
                if n > 0:
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
                else:
                    busy = False
                    next_dep = float('inf')
        win = max(H - warm, 1e-12)
        Ls = area / win
        Ws = (area / max(served, 1e-12)) if served > 0 else 0.0
        bs = busy_area / win
        pl = blk_c / max(arr_c, 1e-12)
        pw = wait_count / max(arr_c, 1e-12)
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(bs)
        per_ploss.append(pl)
        per_pwait.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy_area += busy_area
        tot_wait_area += wait_area
        tot_waiters_area += waiters_area
        tot_served += served
        tot_wait_count += wait_count
        win_total += win
    ns = len(seeds)
    win = win_total / ns
    L = tot_area / win_total
    W = (tot_area / tot_served) if tot_served > 0 else 0.0
    busy_frac = tot_busy_area / win_total
    p_wait = tot_wait_count / max(tot_arr, 1e-12)
    p_loss = tot_blk / max(tot_arr, 1e-12)
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = (tot_dep / ns) / (win / 60.0)
    lam_eff = dep_rate
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'per_seed_p_loss': per_ploss,
        'per_seed_p_wait': per_pwait,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
