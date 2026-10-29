import json, random, argparse, math

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
    for s in range(a.seeds):
        seed = a.seed_start + s
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area_n = 0.0
        area_busy = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait_sum = 0.0
        win_wait_cnt = 0
        last_t = 0.0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if t < H:
                    seg = H - t
                    if t >= warm:
                        area_n += n * seg
                        area_busy += (1 if busy else 0) * seg
                    elif t + seg > warm:
                        seg2 = t + seg - warm
                        area_n += n * seg2
                        area_busy += (1 if busy else 0) * seg2
                break
            if t >= warm:
                area_n += n * dt
                area_busy += (1 if busy else 0) * dt
            elif t + dt > warm:
                seg2 = t + dt - warm
                area_n += n * seg2
                area_busy += (1 if busy else 0) * seg2
            t += dt
            if busy:
                n -= 1
                busy = False
                next_dep = float('inf')
                if t >= warm:
                    win_dep += 1
                if n > 0:
                    busy = True
                    next_dep = t + rng.expovariate(mu)
            else:
                n += 1
                if t >= warm:
                    win_arr += 1
                svc = rng.expovariate(mu)
                busy = True
                next_dep = t + svc
                if t >= warm:
                    win_wait_sum += 0.0
                    win_wait_cnt += 1
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        W = L / (win_arr / win) if win_arr > 0 else 0.0
        pw = 1.0 if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_busy.append(bf)
        per_ploss.append(0.0)
        per_pwait.append(pw)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
    nseeds = a.seeds
    win = H - warm
    L = sum(per_L) / nseeds
    W = sum(per_W) / nseeds
    busy_frac = sum(per_busy) / nseeds
    p_wait = sum(per_pwait) / nseeds
    p_loss = sum(per_ploss) / nseeds
    arr = tot_arr / nseeds
    dep = tot_dep / nseeds
    blk = tot_blk / nseeds
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(nseeds)],
        'seeds_used': nseeds,
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
