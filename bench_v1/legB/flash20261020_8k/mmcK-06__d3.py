import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0
    mu = 10.0
    c = 3
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = c + 1
        cap = cap + 1
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
    tot_busy = 0.0
    tot_util = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_waited = 0.0
    win_total = 0.0
    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        area_wait = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        served_w = 0
        waited_w = 0
        last = 0.0
        while True:
            rate = lam
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                break
            area_n += n * (nt - t)
            area_busy += (1 if n > 0 else 0) * (nt - t)
            area_util += min(n, c) * (nt - t)
            area_wait += len(queue) * (nt - t)
            t = nt
            if t >= warm:
                arr_w += 1
            if n >= cap:
                if t >= warm:
                    blk_w += 1
                continue
            n += 1
            svc = rng.expovariate(mu)
            queue.append((t, svc))
            while queue and busy < c:
                at, sv = queue.pop(0)
                busy += 1
                start = max(at, t)
                end = start + sv
                if end > H:
                    end = H
                if start < H:
                    if start >= warm:
                        served_w += 1
                        if start > at:
                            waited_w += 1
                    if start >= warm:
                        area_wait += (start - at)
                queue.append((end, -1))
                queue = [x for x in queue if x[1] >= 0]
                break
        per_L.append(area_n / H if H > 0 else 0.0)
        per_bf.append(area_busy / H if H > 0 else 0.0)
        per_pl.append(blk_w / arr_w if arr_w > 0 else 0.0)
        per_pw.append(waited_w / served_w if served_w > 0 else 0.0)
        per_W.append(area_wait / served_w if served_w > 0 else 0.0)
        tot_arr += arr_w
        tot_dep += served_w
        tot_blk += blk_w
        tot_busy += area_busy
        tot_util += area_util
        tot_wait += area_wait
        tot_served += served_w
        tot_waited += waited_w
        win_total += H
    seeds_used = a.seeds
    L = sum(per_L) / seeds_used if seeds_used else 0.0
    W = sum(per_W) / seeds_used if seeds_used else 0.0
    busy_frac = sum(per_bf) / seeds_used if seeds_used else 0.0
    p_loss = sum(per_pl) / seeds_used if seeds_used else 0.0
    p_wait = sum(per_pw) / seeds_used if seeds_used else 0.0
    busy_util = (tot_util / win_total) / c if win_total > 0 else 0.0
    arr = tot_arr / seeds_used if seeds_used else 0.0
    dep = tot_dep / seeds_used if seeds_used else 0.0
    blk = tot_blk / seeds_used if seeds_used else 0.0
    dep_rate = (tot_dep / win_total) if win_total > 0 else 0.0
    lam_eff = (tot_arr / win_total) if win_total > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(seeds_used)],
        'seeds_used': seeds_used,
        'time_unit': 'hour',
        'win': H,
        'arr': arr,
        'blk': blk,
        'busy_util': busy_util,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
