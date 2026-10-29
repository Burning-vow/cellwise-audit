import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
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
        dep_time_sum = 0.0
        last_t = 0.0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if t < H:
                    area += n * (H - t)
                    if busy:
                        busy_area += (H - t)
                    waiters_area += n * (H - t)
                break
            if busy:
                t = next_dep
                n -= 1
                dep_c += 1
                dep_time_sum += t
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                t = t + dt
                arr_c += 1
                svc = rng.expovariate(mu)
                if n == 0:
                    n = 1
                    busy = True
                    next_dep = t + svc
                else:
                    n += 1
            area += 0
        # recompute area properly via event integration
        # redo simulation with proper integration
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
        waiters_area = 0.0
        dep_time_sum = 0.0
        wait_sum = 0.0
        wait_count = 0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                area += n * (H - t)
                if busy:
                    busy_area += (H - t)
                waiters_area += n * (H - t)
                break
            area += n * dt
            if busy:
                busy_area += dt
            waiters_area += n * dt
            t = nt
            if busy:
                n -= 1
                dep_c += 1
                dep_time_sum += t
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                arr_c += 1
                svc = rng.expovariate(mu)
                n = 1
                busy = True
                next_dep = t + svc
        # warmup window stats: approximate by running again with warmup tracking
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area_w = 0.0
        busy_area_w = 0.0
        waiters_area_w = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        dep_time_w = 0.0
        wait_sum_w = 0.0
        wait_count_w = 0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                if t < H:
                    seg = H - t
                    if t >= warm:
                        area_w += n * seg
                        if busy:
                            busy_area_w += seg
                        waiters_area_w += n * seg
                    elif nt > warm:
                        seg2 = H - warm
                        area_w += n * seg2
                        if busy:
                            busy_area_w += seg2
                        waiters_area_w += n * seg2
                break
            if t >= warm:
                area_w += n * dt
                if busy:
                    busy_area_w += dt
                waiters_area_w += n * dt
            elif nt > warm:
                seg = nt - warm
                area_w += n * seg
                if busy:
                    busy_area_w += seg
                waiters_area_w += n * seg
            t = nt
            if busy:
                n -= 1
                dep_w += 1
                dep_time_w += t
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                arr_w += 1
                svc = rng.expovariate(mu)
                n = 1
                busy = True
                next_dep = t + svc
        win = H - warm
        Lw = area_w / win if win > 0 else 0.0
        Ww = (waiters_area_w / dep_w) if dep_w > 0 else 0.0
        bw = busy_area_w / win if win > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = wait_count_w / dep_w if dep_w > 0 else 0.0
        per_L.append(Lw)
        per_W.append(Ww)
        per_busy.append(bw)
        per_ploss.append(pl)
        per_pwait.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area_w
        tot_busy_area += busy_area_w
        tot_wait_area += waiters_area_w
        tot_dep_time += dep_time_w
    nseeds = a.seeds
    win = H - warm
    L = (tot_area / win / nseeds) if win > 0 and nseeds > 0 else 0.0
    W = (tot_wait_area / tot_dep) if tot_dep > 0 else 0.0
    busy_frac = (tot_busy_area / win / nseeds) if win > 0 and nseeds > 0 else 0.0
    p_wait = sum(per_pwait) / nseeds if nseeds > 0 else 0.0
    p_loss = sum(per_ploss) / nseeds if nseeds > 0 else 0.0
    arr = tot_arr / nseeds if nseeds > 0 else 0.0
    dep = tot_dep / nseeds if nseeds > 0 else 0.0
    blk = tot_blk / nseeds if nseeds > 0 else 0.0
    dep_rate = (tot_dep / win / nseeds) if win > 0 and nseeds > 0 else 0.0
    lam_eff = dep_rate
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
