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
        lam = lam * 1.25
    elif a.pert == 'mu_up':
        mu = mu * 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    svc = 60.0 / mu

    per_L = []
    per_W = []
    per_busy = []
    per_ploss = []
    per_pwait = []
    seed_list = []

    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy_area = 0.0
    tot_wait_area = 0.0
    tot_wait_n = 0.0
    tot_win = 0.0
    tot_dep_time = 0.0

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam / 60.0)
        last = 0.0
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        wait_n = 0.0
        arr_cnt = 0
        dep_cnt = 0
        blk_cnt = 0
        dep_time_sum = 0.0
        win_start = warm
        win_len = H - warm
        while True:
            if next_arr <= t:
                ev = next_arr
            elif queue:
                ev = queue[0][1]
            else:
                ev = next_arr
            if ev > H:
                dt = H - t
                if t >= win_start:
                    area += n * dt
                    busy_area += (1 if busy > 0 else 0) * dt
                break
            dt = ev - t
            if t >= win_start:
                area += n * dt
                busy_area += (1 if busy > 0 else 0) * dt
            t = ev
            if t == next_arr:
                arr_cnt += 1
                n += 1
                st = rng.expovariate(mu / 60.0) if False else svc
                if busy < c:
                    busy += 1
                    queue.append((st, t + st))
                else:
                    queue.append((st, None))
                next_arr = t + rng.expovariate(lam / 60.0)
            else:
                st, endt = queue.pop(0)
                n -= 1
                dep_cnt += 1
                dep_time_sum += t
                busy -= 1
                if queue:
                    nst, _ = queue[0]
                    queue[0] = (nst, t + nst)
                    busy += 1
        per_L.append(area / win_len if win_len > 0 else 0.0)
        per_busy.append(busy_area / win_len if win_len > 0 else 0.0)
        per_ploss.append(blk_cnt / arr_cnt if arr_cnt > 0 else 0.0)
        per_pwait.append(wait_n / arr_cnt if arr_cnt > 0 else 0.0)
        per_W.append(area / dep_cnt if dep_cnt > 0 else 0.0)
        tot_arr += arr_cnt
        tot_dep += dep_cnt
        tot_blk += blk_cnt
        tot_area += area
        tot_busy_area += busy_area
        tot_wait_area += wait_area
        tot_wait_n += wait_n
        tot_win += win_len
        tot_dep_time += dep_time_sum

    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = tot_area / tot_dep if tot_dep > 0 else 0.0
    busy_frac = tot_busy_area / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / a.seeds
    dep = tot_dep / a.seeds
    blk = tot_blk / a.seeds
    dep_rate = tot_dep / (tot_win / 60.0) if tot_win > 0 else 0.0
    lam_eff = arr / (tot_win / 60.0 / a.seeds) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac / c,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': a.seeds,
        'time_unit': 'minute',
        'win': tot_win / a.seeds,
        'arr': arr,
        'dep': dep,
        'blk': blk,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'per_seed_p_loss': per_ploss,
        'per_seed_p_wait': per_pwait,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
