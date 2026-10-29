import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 12.0
    c = 1
    if a.pert == 'lam_up':
        lam = 7.2
    elif a.pert == 'mu_up':
        mu = 14.4
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
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy_area = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_w = 0.0
    win_total = 0.0

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        n = 0
        busy_until = 0.0
        queue = []
        arr_w = dep_w = blk_w = 0.0
        area = busy_area = 0.0
        wait_sum = 0.0
        waited_cnt = 0
        dep_cnt = 0
        last = 0.0
        while True:
            t += rng.expovariate(lam)
            if t > H:
                break
            dt = t - last
            if t > warm:
                seg = min(dt, t - max(last, warm))
                if seg > 0:
                    area += n * seg
                    busy_area += (1 if n >= c else 0) * seg
            last = t
            if t > warm:
                arr_w += 1
            if n < c:
                n += 1
                busy_until = t + svc
                if t > warm:
                    waited_cnt += 1
            else:
                queue.append(t)
                if t > warm:
                    blk_w += 1
            while n > 0 and busy_until <= t + 1e-12:
                n -= 1
                if queue:
                    qt = queue.pop(0)
                    w = t - qt
                    if t > warm:
                        wait_sum += w
                        dep_cnt += 1
                    n += 1
                    busy_until = t + svc
                else:
                    busy_until = float('inf')
        if n > 0 and busy_until < H:
            pass
        win = H - warm
        win_total += win
        L = area / win if win > 0 else 0.0
        W = (wait_sum / dep_cnt + svc) if dep_cnt > 0 else svc
        bf = busy_area / win if win > 0 else 0.0
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = (arr_w - blk_w) / arr_w if arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_busy.append(bf)
        per_ploss.append(pl)
        per_pwait.append(pw)
        tot_arr += arr_w
        tot_dep += dep_cnt
        tot_blk += blk_w
        tot_area += area
        tot_busy_area += busy_area
        tot_wait += wait_sum
        tot_waited += waited_cnt
        tot_dep_w += dep_cnt

    ns = len(per_L)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    busy_frac = sum(per_busy) / ns
    p_loss = sum(per_ploss) / ns
    p_wait = sum(per_pwait) / ns
    win = win_total / ns
    dep_rate = (tot_dep / win_total) if win_total > 0 else 0.0
    lam_eff = (tot_arr / win_total) if win_total > 0 else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': win,
        'arr': tot_arr / ns,
        'dep': tot_dep / ns,
        'blk': tot_blk / ns,
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
