import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0 / 60.0
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
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_depw = 0.0
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
        arr_c = 0
        dep_c = 0
        blk_c = 0
        wait_sum = 0.0
        waited_c = 0
        depw_sum = 0.0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if busy:
                    area += n * (H - t)
                    busy_area += (H - t)
                else:
                    area += n * (H - t)
                break
            area += n * dt
            if busy:
                busy_area += dt
            t += dt
            if busy and t >= next_dep:
                n -= 1
                dep_c += 1
                if t >= warm:
                    depw_sum += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                arr_c += 1
                svc = rng.expovariate(mu)
                if n == 0:
                    n = 1
                    busy = True
                    next_dep = t + svc
                    if t >= warm:
                        waited_c += 1
                        wait_sum += 0.0
                else:
                    n += 1
                    if t >= warm:
                        waited_c += 1
                        wait_sum += 0.0
        win = H - warm
        Ls = area / H
        Ws = Ls / lam if lam > 0 else 0.0
        bf = busy_area / H
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = waited_c / arr_c if arr_c > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_area
        tot_wait += wait_sum
        tot_waited += waited_c
        tot_depw += depw_sum
        win_total += win
    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    busy_frac = sum(per_bf) / ns
    p_wait = sum(per_pw) / ns
    p_loss = sum(per_pl) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = (tot_dep / ns) / (win_total / ns) if win_total > 0 else 0.0
    lam_eff = dep_rate
    busy_util = busy_frac
    busy_occupied = busy_frac
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win_total / ns,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
