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
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_depw = 0.0
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
        dep_wait_sum = 0.0
        while True:
            if busy:
                dt = next_dep - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area += n * dt
                    busy_area += dt
                t += dt
                if t >= H:
                    break
                n -= 1
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
                arr_w += 1
                svc = rng.expovariate(mu)
                if n == 0:
                    busy = True
                    next_dep = t + svc
                    n = 1
                    if t >= warm:
                        waited_cnt += 1
                        wait_sum += 0.0
                else:
                    n += 1
                    if t >= warm:
                        waited_cnt += 1
                        wait_sum += 0.0
        win = H - warm
        Ls = area / win if win > 0 else 0.0
        Ws = Ls / lam if lam > 0 else 0.0
        bfs = busy_area / win if win > 0 else 0.0
        pls = blk_w / arr_w if arr_w > 0 else 0.0
        pws = waited_cnt / arr_w if arr_w > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        tot_wait += wait_sum
        tot_waited += waited_cnt
        tot_depw += dep_wait_sum
    ns = a.seeds
    win = H - warm
    L = (tot_area / (ns * win)) if win > 0 and ns > 0 else 0.0
    W = L / lam if lam > 0 else 0.0
    busy_frac = (tot_busy / (ns * win)) if win > 0 and ns > 0 else 0.0
    p_wait = (tot_waited / tot_arr) if tot_arr > 0 else 0.0
    p_loss = (tot_blk / tot_arr) if tot_arr > 0 else 0.0
    arr = tot_arr / ns if ns > 0 else 0.0
    dep = tot_dep / ns if ns > 0 else 0.0
    blk = tot_blk / ns if ns > 0 else 0.0
    dep_rate = (tot_dep / (ns * win)) * 60.0 if win > 0 and ns > 0 else 0.0
    lam_eff = (tot_arr / (ns * win)) * 60.0 if win > 0 and ns > 0 else 0.0
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
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'dep': dep,
        'blk': blk,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
