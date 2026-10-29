import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 3
    lam = 8.0 / 60.0
    mu = 1.0 / 12.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 4
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
    tot_wait = 0.0
    tot_served = 0.0
    tot_busy = 0.0
    tot_waitq = 0.0
    tot_arr_w = 0.0
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        seeds.append(s)
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_w = 0
        dep_w = 0
        blk_w = 0
        area_w = 0.0
        wait_w = 0.0
        served_w = 0
        busy_area = 0.0
        waitq_area = 0.0
        last = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            if next_arr <= t:
                ev = next_arr
            else:
                ev = t
            if servers:
                mn = min(servers)
                if mn < ev:
                    ev = mn
            if ev > H:
                dt = H - last
                if last >= warm:
                    area_w += n * dt
                    busy_area += busy * dt
                    waitq_area += len(queue) * dt
                break
            dt = ev - last
            if last >= warm:
                area_w += n * dt
                busy_area += busy * dt
                waitq_area += len(queue) * dt
            last = ev
            t = ev
            if abs(t - next_arr) < 1e-12:
                n += 1
                if t >= warm:
                    arr_w += 1
                st = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    servers.append(t + st)
                    if t >= warm:
                        served_w += 1
                        wait_w += st
                else:
                    queue.append(st)
                next_arr = t + rng.expovariate(lam)
            else:
                servers.sort()
                servers.pop(0)
                busy -= 1
                if t >= warm:
                    dep_w += 1
                if queue:
                    st = queue.pop(0)
                    busy += 1
                    servers.append(t + st)
                    if t >= warm:
                        served_w += 1
                        wait_w += st
        win = H - warm
        Ls = area_w / win if win > 0 else 0.0
        Ws = wait_w / served_w if served_w > 0 else 0.0
        bfs = busy_area / win / c if win > 0 else 0.0
        pls = blk_w / arr_w if arr_w > 0 else 0.0
        pws = waitq_area / win / (arr_w / win) if arr_w > 0 and win > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area_w
        tot_wait += wait_w
        tot_served += served_w
        tot_busy += busy_area
        tot_waitq += waitq_area
        tot_arr_w += arr_w
    ns = len(seeds)
    win = H - warm
    L = tot_area / (win * ns) if win > 0 and ns > 0 else 0.0
    W = tot_wait / tot_served if tot_served > 0 else 0.0
    busy_frac = tot_busy / (win * ns * c) if win > 0 and ns > 0 else 0.0
    p_wait = tot_waitq / (win * ns) / (tot_arr_w / (win * ns)) if tot_arr_w > 0 and win > 0 else 0.0
    arr = tot_arr / ns if ns > 0 else 0.0
    dep = tot_dep / ns if ns > 0 else 0.0
    blk = tot_blk / ns if ns > 0 else 0.0
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': 1.0 - (1.0 - busy_frac) if c > 0 else 0.0,
        'p_wait': p_wait,
        'p_loss': blk / arr if arr > 0 else 0.0,
        'runtime_units': H,
        'seed_list': seeds,
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
