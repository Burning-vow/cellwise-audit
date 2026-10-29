import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 5.0
    c = 2
    cap = 4
    if a.pert == 'lam_up':
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
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
    tot_busy_area = 0.0
    tot_util_area = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_served = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        arr_w = 0
        dep_w = 0
        blk_w = 0
        busy_area = 0.0
        util_area = 0.0
        wait_sum = 0.0
        waited_cnt = 0
        served_cnt = 0
        last = 0.0
        while True:
            dt = rng.expovariate(lam)
            nt = t + dt
            if nt > H:
                if t < H:
                    busy_area += busy * (H - t)
                    util_area += min(busy, c) * (H - t)
                break
            busy_area += busy * (nt - t)
            util_area += min(busy, c) * (nt - t)
            t = nt
            n += 1
            svc = rng.expovariate(mu)
            if busy < c and len(queue) == 0:
                busy += 1
                queue.append((t, svc, t + svc))
            elif len(queue) + busy < cap:
                queue.append((t, svc, None))
            else:
                if t >= warm:
                    blk_w += 1
            if t >= warm:
                arr_w += 1
            while True:
                started = None
                for i, (at, sv, st) in enumerate(queue):
                    if st is None and busy < c:
                        started = i
                        break
                if started is None:
                    break
                at, sv, _ = queue.pop(started)
                busy += 1
                queue.append((at, sv, t + sv))
            done = [q for q in queue if q[2] is not None and q[2] <= t]
            for q in done:
                queue.remove(q)
                busy -= 1
                if q[2] >= warm:
                    dep_w += 1
                    served_cnt += 1
                    wait_sum += (q[2] - q[1]) - q[0]
                    waited_cnt += 1
            while True:
                started = None
                for i, (at, sv, st) in enumerate(queue):
                    if st is None and busy < c:
                        started = i
                        break
                if started is None:
                    break
                at, sv, _ = queue.pop(started)
                busy += 1
                queue.append((at, sv, t + sv))
        win = H - warm
        win_total += win
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_busy_area += busy_area
        tot_util_area += util_area
        tot_wait += wait_sum
        tot_waited += waited_cnt
        tot_served += served_cnt
        Ls = busy_area / H
        Ws = (wait_sum / served_cnt) if served_cnt > 0 else 0.0
        bfs = busy_area / H
        pls = blk_w / arr_w if arr_w > 0 else 0.0
        pws = waited_cnt / arr_w if arr_w > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)

    L = tot_busy_area / (win_total if win_total > 0 else 1.0)
    W = (tot_wait / tot_served) if tot_served > 0 else 0.0
    busy_frac = tot_busy_area / (win_total if win_total > 0 else 1.0)
    busy_util = tot_util_area / (win_total * c if win_total > 0 else 1.0)
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_waited / tot_arr if tot_arr > 0 else 0.0
    dep_rate = tot_dep / (win_total if win_total > 0 else 1.0)
    lam_eff = tot_arr / (win_total if win_total > 0 else 1.0)

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'p_loss': p_loss,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'hour',
        'win': win_total / len(seeds) if seeds else 0.0,
        'arr': tot_arr / len(seeds) if seeds else 0.0,
        'blk': tot_blk / len(seeds) if seeds else 0.0,
        'busy_util': busy_util,
        'busy_occupied': busy_frac,
        'dep': tot_dep / len(seeds) if seeds else 0.0,
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
