import json, random, argparse, math

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
    tot_dep_time = 0.0
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        seeds.append(s)
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        arr_c = 0
        dep_c = 0
        blk_c = 0
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        waiters_area = 0.0
        served = 0
        wait_count = 0
        dep_time_sum = 0.0
        while True:
            if n == 0:
                dt = rng.expovariate(lam)
                t_next = t + dt
                if t_next > H:
                    area += n * (H - t)
                    busy_area += (1 if busy else 0) * (H - t)
                    waiters_area += max(n - 1, 0) * (H - t)
                    break
                area += n * (t_next - t)
                busy_area += (1 if busy else 0) * (t_next - t)
                waiters_area += max(n - 1, 0) * (t_next - t)
                t = t_next
                arr_c += 1
                n = 1
                busy = True
                svc = rng.expovariate(mu)
                next_dep = t + svc
            else:
                dt_arr = rng.expovariate(lam)
                t_arr = t + dt_arr
                t_dep = next_dep
                t_next = min(t_arr, t_dep)
                if t_next > H:
                    area += n * (H - t)
                    busy_area += (1 if busy else 0) * (H - t)
                    waiters_area += max(n - 1, 0) * (H - t)
                    break
                area += n * (t_next - t)
                busy_area += (1 if busy else 0) * (t_next - t)
                waiters_area += max(n - 1, 0) * (t_next - t)
                t = t_next
                if t_arr <= t_dep:
                    arr_c += 1
                    n += 1
                    svc = rng.expovariate(mu)
                    if n == 1:
                        busy = True
                        next_dep = t + svc
                else:
                    dep_c += 1
                    served += 1
                    dep_time_sum += t
                    n -= 1
                    if n == 0:
                        busy = False
                        next_dep = float('inf')
                    else:
                        svc = rng.expovariate(mu)
                        next_dep = t + svc
        win = H - warm
        if win <= 0:
            win = H
            warm = 0.0
        Ls = area / H
        Ws = Ls / (lam * (1 - 0)) if lam > 0 else 0.0
        busy_s = busy_area / H
        ploss_s = 0.0
        pwait_s = 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(busy_s)
        per_ploss.append(ploss_s)
        per_pwait.append(pwait_s)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy_area += busy_area
        tot_wait_area += wait_area
        tot_waiters_area += waiters_area
        tot_served += served
        tot_wait_count += wait_count
        tot_dep_time += dep_time_sum
    ns = len(seeds)
    L = tot_area / (H * ns)
    busy_frac = tot_busy_area / (H * ns)
    lam_eff = tot_dep / (H * ns)
    W = L / lam_eff if lam_eff > 0 else 0.0
    p_wait = 0.0
    p_loss = 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = tot_dep / (H * ns) * 60.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': H,
        'arr': arr,
        'dep': dep,
        'blk': blk,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'per_seed_p_loss': per_ploss,
        'per_seed_p_wait': per_pwait,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
