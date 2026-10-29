import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
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
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_w = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        waited_cnt = 0
        dep_w_sum = 0.0
        while True:
            if busy:
                dt = next_dep - t
                if t + dt > H:
                    dt = H - t
                    if t >= warm:
                        area += n * dt
                        busy_area += dt
                    t = H
                    break
                if t >= warm:
                    area += n * dt
                    busy_area += dt
                t = next_dep
                n -= 1
                if t >= warm:
                    dep_w += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                dt = rng.expovariate(lam)
                if t + dt > H:
                    if t >= warm:
                        area += n * (H - t)
                    t = H
                    break
                if t >= warm:
                    area += n * dt
                t += dt
                if t >= warm:
                    arr_w += 1
                n += 1
                busy = True
                next_dep = t + rng.expovariate(mu)
        win = H - warm
        L = area / win if win > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        W = L / (lam * (1.0 - 0.0)) if lam > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(bf)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        tot_wait += wait_sum
        tot_waited += waited_cnt
        tot_dep_w += dep_w_sum
    ns = a.seeds
    win = H - warm
    L = tot_area / (win * ns) if win > 0 and ns > 0 else 0.0
    busy_frac = tot_busy / (win * ns) if win > 0 and ns > 0 else 0.0
    lam_eff = lam
    W = L / lam_eff if lam_eff > 0 else 0.0
    dep_rate = tot_dep / (win * ns) if win > 0 and ns > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': busy_frac,
        'runtime_units': 'minute',
        'seed_list': seed_list,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': tot_arr / ns if ns > 0 else 0.0,
        'blk': tot_blk / ns if ns > 0 else 0.0,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'dep': tot_dep / ns if ns > 0 else 0.0,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
