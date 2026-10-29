import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    c = 1
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area_N = tot_area_busy = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_wait_n = 0
    tot_served = 0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        servers = [0.0] * c
        queue = []
        arr_c = dep_c = blk_c = 0
        area_N = area_busy = 0.0
        wait_sum = 0.0
        wait_n = 0
        served = 0
        last = 0.0
        while t < H:
            if next_arr <= t:
                dt = next_arr - last
                if next_arr >= warm:
                    area_N += n * dt
                    area_busy += busy * dt
                last = next_arr
                t = next_arr
                if t >= H:
                    break
                arr_c += 1
                st = rng.expovariate(mu)
                cust = {'arr': t, 'st': st}
                if busy < c:
                    busy += 1
                    idx = servers.index(min(servers))
                    servers[idx] = t + st
                    cust['start'] = t
                    if t >= warm:
                        wait_sum += 0.0
                        wait_n += 1
                        served += 1
                else:
                    queue.append(cust)
                n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                tnext = min(servers) if busy > 0 else float('inf')
                if tnext == float('inf'):
                    t = next_arr
                    continue
                dt = tnext - last
                if tnext >= warm:
                    area_N += n * dt
                    area_busy += busy * dt
                last = tnext
                t = tnext
                if t >= H:
                    break
                idx = servers.index(min(servers))
                servers[idx] = float('inf')
                busy -= 1
                dep_c += 1
                n -= 1
                if queue:
                    cust = queue.pop(0)
                    busy += 1
                    servers[idx] = t + cust['st']
                    if t >= warm:
                        wait_sum += t - cust['arr']
                        wait_n += 1
                        served += 1
        dt = H - last
        if dt > 0:
            area_N += n * dt
            area_busy += busy * dt
        win = H - warm
        L = area_N / win if win > 0 else 0.0
        bf = area_busy / (win * c) if win > 0 else 0.0
        W = wait_sum / wait_n if wait_n > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = (arr_c - served) / arr_c if arr_c > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area_N += area_N
        tot_area_busy += area_busy
        tot_win += win
        tot_wait += wait_sum
        tot_wait_n += wait_n
        tot_served += served

    ns = len(seeds)
    L = tot_area_N / tot_win if tot_win > 0 else 0.0
    W = tot_wait / tot_wait_n if tot_wait_n > 0 else 0.0
    busy_frac = tot_area_busy / (tot_win * c) if tot_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = (tot_dep / ns) / (tot_win / ns) * 60.0 if tot_win > 0 else 0.0
    lam_eff = (tot_arr / ns) / (tot_win / ns) * 60.0 if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = (tot_arr - tot_served) / tot_arr if tot_arr > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': tot_win / ns,
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
