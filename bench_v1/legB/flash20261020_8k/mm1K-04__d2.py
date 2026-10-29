import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 5.0
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        K = 5
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
    tot_occ = 0.0
    tot_wait = 0.0
    tot_waitn = 0.0
    tot_serv = 0.0
    win_total = 0.0
    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        busy = False
        busy_end = 0.0
        queue = []
        arr = 0
        dep = 0
        blk = 0
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        area_wait = 0.0
        waitn = 0
        serv_sum = 0.0
        last = 0.0
        while True:
            if busy:
                dt = busy_end - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area_n += n * dt
                    area_busy += dt
                    area_occ += min(n, K) * dt
                t += dt
                if t >= H:
                    break
                n -= 1
                busy = False
                dep += 1
                if queue:
                    q = queue.pop(0)
                    st = q[1]
                    serv_sum += t - st
                    if t >= warm:
                        area_wait += (t - st)
                        waitn += 1
                    busy = True
                    busy_end = t + q[0]
            else:
                dt = rng.expovariate(lam)
                if t + dt > H:
                    if t >= warm:
                        area_n += n * (H - t)
                        area_occ += min(n, K) * (H - t)
                    t = H
                    break
                t += dt
                if t >= warm:
                    area_n += n * dt
                    area_occ += min(n, K) * dt
                arr += 1
                st = rng.expovariate(mu)
                if n < K:
                    n += 1
                    if not busy:
                        busy = True
                        busy_end = t + st
                    else:
                        queue.append((st, t))
                else:
                    blk += 1
        win = H - warm
        win_total += win
        per_L.append(area_n / win if win > 0 else 0.0)
        per_bf.append(area_busy / win if win > 0 else 0.0)
        per_pl.append(blk / arr if arr > 0 else 0.0)
        per_pw.append(waitn / arr if arr > 0 else 0.0)
        per_W.append(area_wait / waitn if waitn > 0 else 0.0)
        tot_arr += arr
        tot_dep += dep
        tot_blk += blk
        tot_busy += area_busy
        tot_occ += area_occ
        tot_wait += area_wait
        tot_waitn += waitn
        tot_serv += serv_sum
    L = sum(per_L) / a.seeds
    W = sum(per_W) / a.seeds
    bf = sum(per_bf) / a.seeds
    pl = sum(per_pl) / a.seeds
    pw = sum(per_pw) / a.seeds
    win = win_total / a.seeds
    arr_avg = tot_arr / a.seeds
    dep_avg = tot_dep / a.seeds
    blk_avg = tot_blk / a.seeds
    busy_util = (tot_occ / win_total) / K if win_total > 0 else 0.0
    dep_rate = dep_avg / win if win > 0 else 0.0
    lam_eff = arr_avg / win if win > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': [a.seed_start + i for i in range(a.seeds)],
        'seeds_used': a.seeds,
        'time_unit': 'minute',
        'win': win,
        'arr': arr_avg,
        'blk': blk_avg,
        'busy_util': busy_util,
        'busy_occupied': bf,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
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
