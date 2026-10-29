import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 2
    lam = 14.0 / 60.0
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 3
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
    tot_win = 0.0
    tot_busy = 0.0
    tot_occ = 0.0
    tot_wait = 0.0
    tot_serv = 0.0
    tot_n = 0
    tot_depw = 0.0
    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        serv_sum = 0.0
        n_dep = 0
        last = 0.0
        while True:
            if n == 0:
                dt = rng.expovariate(lam)
                nt = t + dt
            else:
                dt = rng.expovariate(lam + busy * mu)
                nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                    area_occ += (1 if busy > 0 else 0) * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            area_occ += (1 if busy > 0 else 0) * (nt - t)
            t = nt
            if rng.random() < lam / (lam + busy * mu):
                n += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    if t >= warm:
                        arr_w += 1
                        serv_sum += svc
                        n_dep += 1
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        arr_w += 1
                        blk_w += 1
            else:
                busy -= 1
                servers.remove(min(servers))
                if queue:
                    at, svc = queue.pop(0)
                    busy += 1
                    servers.append(t + svc)
                    if t >= warm:
                        wait_sum += t - at
                        serv_sum += svc
                        n_dep += 1
                if t >= warm:
                    dep_w += 1
        win = H - warm
        L = area_n / H
        bf = area_busy / (c * H)
        occ = area_occ / H
        W = (wait_sum + serv_sum) / n_dep if n_dep > 0 else 0.0
        pw = blk_w / arr_w if arr_w > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_win += win
        tot_busy += area_busy
        tot_occ += area_occ
        tot_wait += wait_sum
        tot_serv += serv_sum
        tot_n += n_dep
        tot_depw += dep_w
    seeds_used = a.seeds
    L = sum(per_L) / seeds_used
    W = sum(per_W) / seeds_used
    bf = sum(per_bf) / seeds_used
    pw = sum(per_pw) / seeds_used
    pl = sum(per_pl) / seeds_used
    arr = tot_arr / seeds_used
    dep = tot_dep / seeds_used
    blk = tot_blk / seeds_used
    win = tot_win / seeds_used
    dep_rate = dep / win * 60.0 if win > 0 else 0.0
    busy_util = bf
    busy_occupied = tot_occ / (seeds_used * H)
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(seeds_used)],
        'seeds_used': seeds_used,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_loss': pl,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
