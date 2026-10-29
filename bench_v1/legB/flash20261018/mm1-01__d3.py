import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
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
    tot_served = 0.0
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
        busy_t = 0.0
        wait_sum = 0.0
        waited_c = 0
        served_c = 0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if t < H:
                    area += n * (H - t)
                    if busy:
                        busy_t += (H - t)
                break
            area += n * dt
            if busy:
                busy_t += dt
            t += dt
            if busy and t >= next_dep:
                n -= 1
                dep_c += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                arr_c += 1
                if n == 0:
                    st = rng.expovariate(mu)
                    n = 1
                    busy = True
                    next_dep = t + st
                    if t >= warm:
                        wait_sum += 0.0
                        waited_c += 1
                        served_c += 1
                else:
                    st = rng.expovariate(mu)
                    n += 1
                    if t >= warm:
                        wait_sum += st
                        waited_c += 1
                        served_c += 1
        win = H - warm
        Ls = area / H
        Ws = Ls / lam if lam > 0 else 0.0
        bfs = busy_t / H
        pls = blk_c / arr_c if arr_c > 0 else 0.0
        pws = waited_c / served_c if served_c > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_busy += busy_t
        tot_wait += wait_sum
        tot_waited += waited_c
        tot_served += served_c
    ns = len(seeds)
    L = tot_area / (H * ns)
    W = L / lam if lam > 0 else 0.0
    busy_frac = tot_busy / (H * ns)
    p_wait = tot_waited / tot_served if tot_served > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / H
    lam_eff = arr / H
    p_loss = blk / arr if arr > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': arr,
        'dep': dep,
        'blk': blk,
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
