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
    tot_wait_cnt = 0.0
    tot_win = 0.0
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
        num_area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_cnt = 0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if t < H:
                    seg = H - t
                    if t >= warm:
                        num_area += n * seg
                        busy_area += (1.0 if busy else 0.0) * seg
                    elif t + seg > warm:
                        seg2 = t + seg - warm
                        num_area += n * seg2
                        busy_area += (1.0 if busy else 0.0) * seg2
                break
            if t >= warm:
                num_area += n * dt
                busy_area += (1.0 if busy else 0.0) * dt
            elif t + dt > warm:
                seg2 = t + dt - warm
                num_area += n * seg2
                busy_area += (1.0 if busy else 0.0) * seg2
            t += dt
            if busy:
                n -= 1
                dep_c += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                arr_c += 1
                svc = rng.expovariate(mu)
                n += 1
                busy = True
                next_dep = t + svc
                if t >= warm:
                    wait_area += svc
                    wait_cnt += 1
        win = H - warm
        Ls = num_area / win if win > 0 else 0.0
        Ws = wait_area / wait_cnt if wait_cnt > 0 else 0.0
        bs = busy_area / win if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = wait_cnt / arr_c if arr_c > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_busy.append(bs)
        per_ploss.append(pl)
        per_pwait.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_busy_area += busy_area
        tot_num_area += num_area
        tot_wait_area += wait_area
        tot_wait_cnt += wait_cnt
        tot_win += win
    nseeds = len(seeds)
    L = tot_num_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait_area / tot_wait_cnt if tot_wait_cnt > 0 else 0.0
    busy_frac = tot_busy_area / tot_win if tot_win > 0 else 0.0
    p_wait = tot_wait_cnt / tot_arr if tot_arr > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    arr_avg = tot_arr / nseeds
    dep_avg = tot_dep / nseeds
    blk_avg = tot_blk / nseeds
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    lam_eff = arr_avg / (tot_win / nseeds) if tot_win > 0 else 0.0
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
        'seeds_used': nseeds,
        'time_unit': 'minute',
        'win': tot_win / nseeds if nseeds > 0 else 0.0,
        'arr': arr_avg,
        'dep': dep_avg,
        'blk': blk_avg,
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
