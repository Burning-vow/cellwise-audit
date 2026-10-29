import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0
    mu = 10.0
    c = 2
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = c + 1
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
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_times = []
        dep_times = []
        blk = 0
        area_n = 0.0
        area_busy = 0.0
        area_q = 0.0
        wait_sum = 0.0
        wait_cnt = 0
        wait_events = 0
        arr_cnt = 0
        dep_cnt = 0
        last_t = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            if servers:
                next_dep = min(servers)
            else:
                next_dep = float('inf')
            if next_arr < next_dep:
                nt = next_arr
            else:
                nt = next_dep
            if nt > H:
                dt = H - last_t
                area_n += n * dt
                area_busy += busy * dt
                area_q += len(queue) * dt
                last_t = H
                break
            dt = nt - last_t
            area_n += n * dt
            area_busy += busy * dt
            area_q += len(queue) * dt
            last_t = nt
            t = nt
            if next_arr <= next_dep:
                arr_cnt += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    if t >= warm:
                        wait_sum += 0.0
                        wait_cnt += 1
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        wait_events += 1
                n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                servers.remove(next_dep)
                busy -= 1
                n -= 1
                dep_cnt += 1
                if queue:
                    at, svc = queue.pop(0)
                    busy += 1
                    servers.append(t + svc)
                    n += 1
                    w = t - at
                    if t >= warm:
                        wait_sum += w + svc
                        wait_cnt += 1
                else:
                    if t >= warm:
                        pass
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / (c * win) if win > 0 else 0.0
        W = wait_sum / wait_cnt if wait_cnt > 0 else 0.0
        pw = wait_events / arr_cnt if arr_cnt > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        tot_arr += arr_cnt
        tot_dep += dep_cnt
        tot_blk += blk
    seeds_used = a.seeds
    L = sum(per_L) / seeds_used if seeds_used else 0.0
    W = sum(per_W) / seeds_used if seeds_used else 0.0
    bf = sum(per_bf) / seeds_used if seeds_used else 0.0
    pw = sum(per_pw) / seeds_used if seeds_used else 0.0
    arr = tot_arr / seeds_used if seeds_used else 0.0
    dep = tot_dep / seeds_used if seeds_used else 0.0
    blk = tot_blk / seeds_used if seeds_used else 0.0
    win = H - warm
    dep_rate = dep / win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_wait': pw,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'hour',
        'win': win,
        'arr': arr,
        'blk': blk,
        'busy_util': bf,
        'busy_occupied': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam,
        'p_loss': 0.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
