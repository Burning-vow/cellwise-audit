import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 5.0
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
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy_time = 0.0
    tot_util_area = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_win = 0
        dep_win = 0
        blk_win = 0
        busy_area = 0.0
        util_area = 0.0
        wait_sum = 0.0
        waited_cnt = 0
        last_t = 0.0
        while True:
            dt = rng.expovariate(lam)
            t_next = t + dt
            if t_next > H:
                break
            busy_area += busy * (t_next - t)
            util_area += min(busy, c) * (t_next - t)
            t = t_next
            n += 1
            svc = rng.expovariate(mu)
            if busy < c and len(queue) == 0:
                busy += 1
                servers.append(t + svc)
                if t >= warm:
                    arr_win += 1
                    wait_sum += 0.0
                    waited_cnt += 1
            elif len(queue) + busy < cap:
                queue.append((t, svc))
                if t >= warm:
                    arr_win += 1
            else:
                if t >= warm:
                    arr_win += 1
                    blk_win += 1
            while servers and servers[0] <= t:
                servers.pop(0)
                busy -= 1
                if t >= warm:
                    dep_win += 1
                if queue:
                    at, sv = queue.pop(0)
                    w = t - at
                    if t >= warm:
                        wait_sum += w
                        waited_cnt += 1
                    busy += 1
                    servers.append(t + sv)
                    servers.sort()
        busy_area += busy * (H - t)
        util_area += min(busy, c) * (H - t)
        win = H - warm
        L = busy_area / H
        W = (wait_sum / waited_cnt) if waited_cnt > 0 else 0.0
        bf = busy_area / H
        pl = blk_win / arr_win if arr_win > 0 else 0.0
        pw = waited_cnt / arr_win if arr_win > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_win
        tot_dep += dep_win
        tot_blk += blk_win
        tot_busy_time += busy_area
        tot_util_area += util_area
        tot_win += win
        tot_wait += wait_sum
        tot_waited += waited_cnt
        tot_dep_win += dep_win

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    busy_frac = sum(per_bf) / ns
    p_loss = sum(per_pl) / ns
    p_wait = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = (tot_dep / tot_win) if tot_win > 0 else 0.0
    busy_util = (tot_util_area / (c * tot_win)) if tot_win > 0 else 0.0
    lam_eff = (tot_arr / tot_win) if tot_win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
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
