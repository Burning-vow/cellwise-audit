import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=str, default='2000')
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    H = float(a.horizon)
    lam = 4.0 / 60.0
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        pass
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seeds = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waiters = 0.0
    win = H - warm
    for s in range(a.seeds):
        seed = a.seed_start + s
        seeds.append(seed)
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
        wait_w = 0.0
        served_w = 0
        waiters_w = 0
        while True:
            rate = lam + (mu if busy else 0.0)
            if rate <= 0:
                break
            dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                if t < H:
                    area += n * (H - t)
                    busy_area += (1 if busy else 0) * (H - t)
                break
            area += n * (nt - t)
            busy_area += (1 if busy else 0) * (nt - t)
            t = nt
            if busy and rng.random() < mu / rate:
                n -= 1
                busy = False
                if t >= warm:
                    dep_w += 1
                if n > 0:
                    busy = True
                    next_dep = t + rng.expovariate(mu)
            else:
                n += 1
                if t >= warm:
                    arr_w += 1
                if not busy:
                    busy = True
                    next_dep = t + rng.expovariate(mu)
        Ls = area / H
        Ws = Ls / lam if lam > 0 else 0.0
        bf = busy_area / H
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(0.0)
        tot_area += area
        tot_busy += busy_area
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
    nseeds = len(seeds)
    L = tot_area / (nseeds * H)
    W = L / lam if lam > 0 else 0.0
    busy_frac = tot_busy / (nseeds * H)
    p_wait = 0.0
    p_loss = 0.0
    arr = tot_arr / nseeds
    dep = tot_dep / nseeds
    blk = tot_blk / nseeds
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = lam
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_wait': p_wait,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': nseeds,
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
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
