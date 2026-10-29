import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 7.0 / 60.0
    mu = 1.0 / 6.0
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
    tot_busy_area = 0.0
    tot_num_area = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0
    seed_list = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        seed_list.append(s)
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        next_dep = float('inf')
        arr_c = 0
        dep_c = 0
        blk_c = 0
        busy_area = 0.0
        num_area = 0.0
        wait_area = 0.0
        wait_n = 0.0
        while True:
            if next_arr <= next_dep:
                tnext = next_arr
                ev = 0
            else:
                tnext = next_dep
                ev = 1
            if tnext > H:
                dt = H - t
                if dt > 0:
                    busy_area += busy * dt
                    num_area += n * dt
                break
            dt = tnext - t
            if t >= warm:
                busy_area += busy * dt
                num_area += n * dt
            t = tnext
            if ev == 0:
                arr_c += 1
                svc = rng.expovariate(mu)
                if busy == 0:
                    busy = 1
                    next_dep = t + svc
                    if t >= warm:
                        wait_area += 0.0
                        wait_n += 1
                else:
                    n += 1
                    if t >= warm:
                        wait_area += 0.0
                        wait_n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                dep_c += 1
                if n > 0:
                    n -= 1
                    svc = rng.expovariate(mu)
                    next_dep = t + svc
                else:
                    busy = 0
                    next_dep = float('inf')
        win = H - warm
        tot_win += win
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_busy_area += busy_area
        tot_num_area += num_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        Ls = num_area / win if win > 0 else 0.0
        Ws = Ls / (dep_c / win) if dep_c > 0 else 0.0
        bs = busy_area / win if win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(bs)
        per_ploss.append(0.0)
        per_pwait.append(0.0)
    win = tot_win / a.seeds if a.seeds > 0 else 0.0
    L = tot_num_area / tot_win if tot_win > 0 else 0.0
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    busy_frac = tot_busy_area / tot_win if tot_win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': 0.0,
        'p_loss': 0.0,
        'runtime_units': 'minute',
        'time_unit': 'minute',
        'seed_list': seed_list,
        'seeds_used': len(seed_list),
        'win': win,
        'arr': tot_arr / a.seeds if a.seeds > 0 else 0.0,
        'dep': tot_dep / a.seeds if a.seeds > 0 else 0.0,
        'blk': tot_blk / a.seeds if a.seeds > 0 else 0.0,
        'dep_rate': dep_rate * 60.0,
        'lam_eff': lam * 60.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'per_seed_p_loss': per_ploss,
        'per_seed_p_wait': per_pwait,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
