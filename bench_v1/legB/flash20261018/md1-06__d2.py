import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = 8.0 * 1.25
    elif a.pert == 'mu_up':
        mu = 12.0 * 1.25
    elif a.pert == 'c_up':
        c = 2

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
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_served = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        served_w = 0
        last = 0.0
        win_start = warm
        win_len = H - warm
        while t < H:
            if next_arr <= t:
                dt = next_arr - last
                if t > win_start:
                    area += n * dt
                    busy_area += (1 if busy >= c else 0) * dt
                last = next_arr
                t = next_arr
                if t > win_start:
                    arr_w += 1
                if busy < c:
                    busy += 1
                    st = rng.expovariate(mu)
                    queue.append((t + st, t))
                else:
                    queue.append((None, t))
                next_arr = t + rng.expovariate(lam)
            else:
                if not queue:
                    dt = min(next_arr, H) - last
                    if t > win_start:
                        area += n * dt
                        busy_area += (1 if busy >= c else 0) * dt
                    last = min(next_arr, H)
                    t = min(next_arr, H)
                    continue
                dep_t, arr_t = queue[0]
                if dep_t is None:
                    dt = min(next_arr, H) - last
                    if t > win_start:
                        area += n * dt
                        busy_area += (1 if busy >= c else 0) * dt
                    last = min(next_arr, H)
                    t = min(next_arr, H)
                    continue
                dt = dep_t - last
                if dep_t > win_start:
                    area += n * dt
                    busy_area += (1 if busy >= c else 0) * dt
                last = dep_t
                t = dep_t
                queue.pop(0)
                busy -= 1
                n -= 1
                if t > win_start:
                    dep_w += 1
                    served_w += 1
                    wait_area += (t - arr_t)
                    wait_n += 1
                if queue:
                    nd, na = queue[0]
                    if nd is None:
                        queue[0] = (t + rng.expovariate(mu), na)
                        busy += 1
                        n += 1
        Ls = area / win_len if win_len > 0 else 0.0
        Ws = (wait_area / wait_n) if wait_n > 0 else 0.0
        bfs = busy_area / win_len if win_len > 0 else 0.0
        pls = blk_w / arr_w if arr_w > 0 else 0.0
        pws = wait_n / arr_w if arr_w > 0 else 0.0
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
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_served += served_w
        tot_win += win_len

    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_wait_area / tot_wait_n if tot_wait_n > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    lam_eff = tot_arr / (tot_win / 60.0) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': len(seeds),
        'time_unit': 'minute',
        'win': tot_win / len(seeds),
        'arr': arr,
        'dep': dep,
        'blk': blk,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
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
