import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    svc = 60.0 / mu

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        queue = []
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0.0
        arr_w = dep_w = blk_w = 0.0
        last = 0.0
        while t < H:
            if next_arr <= t:
                dt = next_arr - last
                if next_arr >= warm:
                    area += n * dt
                    busy_area += (1 if n >= c else 0) * dt
                last = next_arr
                t = next_arr
                if n >= c:
                    blk_w += 1
                else:
                    n += 1
                    arr_w += 1
                    sv = svc
                    queue.append((t, sv))
                next_arr = t + rng.expovariate(lam)
            else:
                if queue:
                    st, sv = queue[0]
                    end = st + sv
                    if end <= next_arr:
                        dt = end - last
                        if end >= warm:
                            area += n * dt
                            busy_area += (1 if n >= c else 0) * dt
                        last = end
                        t = end
                        queue.pop(0)
                        n -= 1
                        dep_w += 1
                        if st >= warm:
                            wait_area += (st - st) * 0
                        continue
                dt = next_arr - last
                if next_arr >= warm:
                    area += n * dt
                    busy_area += (1 if n >= c else 0) * dt
                last = next_arr
                t = next_arr
                if n >= c:
                    blk_w += 1
                else:
                    n += 1
                    arr_w += 1
                    queue.append((t, svc))
                next_arr = t + rng.expovariate(lam)
        win = H - warm
        L = area / win if win > 0 else 0.0
        bf = busy_area / win if win > 0 else 0.0
        W = L / (dep_w / win) if dep_w > 0 else 0.0
        pl = blk_w / (arr_w + blk_w) if (arr_w + blk_w) > 0 else 0.0
        pw = 1.0 if c == 1 and arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        tot_win += win

    ns = len(per_L)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bf,
        'busy_occupied': bf,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': arr,
        'blk': blk,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': pl,
        'p_wait': pw,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
