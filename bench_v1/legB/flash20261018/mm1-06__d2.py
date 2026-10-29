import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=20000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 7.0 / 60.0
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
    seed_list = []
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
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
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
                svc = rng.expovariate(mu)
                n = 1
                busy = True
                next_dep = t + svc
                arr_c += 1
                if t >= warm:
                    pass
            else:
                dt_arr = rng.expovariate(lam)
                t_arr = t + dt_arr
                t_dep = next_dep
                if t_arr < t_dep:
                    if t_arr > H:
                        area += n * (H - t)
                        busy_area += (1 if busy else 0) * (H - t)
                        waiters_area += max(n - 1, 0) * (H - t)
                        break
                    area += n * (t_arr - t)
                    busy_area += (1 if busy else 0) * (t_arr - t)
                    waiters_area += max(n - 1, 0) * (t_arr - t)
                    t = t_arr
                    svc = rng.expovariate(mu)
                    n += 1
                    arr_c += 1
                else:
                    if t_dep > H:
                        area += n * (H - t)
                        busy_area += (1 if busy else 0) * (H - t)
                        waiters_area += max(n - 1, 0) * (H - t)
                        break
                    area += n * (t_dep - t)
                    busy_area += (1 if busy else 0) * (t_dep - t)
                    waiters_area += max(n - 1, 0) * (t_dep - t)
                    t = t_dep
                    n -= 1
                    dep_c += 1
                    if t >= warm:
                        served += 1
                        dep_time_sum += t
                    if n > 0:
                        svc = rng.expovariate(mu)
                        next_dep = t + svc
                        busy = True
                    else:
                        busy = False
                        next_dep = float('inf')
        win = H - warm
        L_est = area / H
        W_est = (area / H) / (lam * (1.0)) if lam > 0 else 0.0
        busy_est = busy_area / H
        ploss_est = 0.0
        pwait_est = 0.0
        per_L.append(L_est)
        per_W.append(W_est)
        per_busy.append(busy_est)
        per_ploss.append(ploss_est)
        per_pwait.append(pwait_est)
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
    n_seeds = a.seeds
    L = sum(per_L) / n_seeds
    W = sum(per_W) / n_seeds
    busy_frac = sum(per_busy) / n_seeds
    p_wait = sum(per_pwait) / n_seeds
    p_loss = sum(per_ploss) / n_seeds
    arr = tot_arr / n_seeds
    dep = tot_dep / n_seeds
    blk = tot_blk / n_seeds
    win = H - warm
    dep_rate = (tot_dep / n_seeds) / win * 60.0 if win > 0 else 0.0
    lam_eff = lam * 60.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n_seeds,
        'time_unit': 'minute',
        'win': win,
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
