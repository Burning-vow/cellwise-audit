import json, random, argparse, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 7.0 / 60.0
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
    per_busy = []
    per_ploss = []
    per_pwait = []
    seed_list = []
    t0 = time.time()
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area_n = 0.0
        area_busy = 0.0
        win_area_n = 0.0
        win_area_busy = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait = 0
        win_served = 0
        win_wait_sum = 0.0
        last_t = 0.0
        while t < H:
            rate = lam + (mu if busy else 0.0)
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                nt = H
            if nt > warm:
                seg_start = max(t, warm)
                seg = nt - seg_start
                win_area_n += n * seg
                win_area_busy += (1 if busy else 0) * seg
            t = nt
            if t >= H:
                break
            if busy and rng.random() < mu / rate:
                n -= 1
                busy = False
                if t > warm:
                    win_dep += 1
            else:
                if t > warm:
                    win_arr += 1
                if n == 0:
                    n = 1
                    busy = True
                    serv = rng.expovariate(mu)
                    if t > warm:
                        win_served += 1
                        win_wait_sum += serv
                else:
                    if t > warm:
                        win_blk += 1
        win = H - warm
        L = win_area_n / win if win > 0 else 0.0
        bf = win_area_busy / win if win > 0 else 0.0
        W = L / lam if lam > 0 else 0.0
        ploss = win_blk / win_arr if win_arr > 0 else 0.0
        pwait = 1.0 - (win_served / win_arr) if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_busy.append(bf)
        per_ploss.append(ploss)
        per_pwait.append(pwait)
    n_seeds = len(per_L)
    def avg(x):
        return sum(x) / len(x) if x else 0.0
    L = avg(per_L)
    W = avg(per_W)
    busy_frac = avg(per_busy)
    p_loss = avg(per_ploss)
    p_wait = avg(per_pwait)
    win = H - warm
    dep_rate = lam * (1.0 - p_loss) * 60.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'p_loss': p_loss,
        'runtime_units': time.time() - t0,
        'seed_list': seed_list,
        'seeds_used': n_seeds,
        'time_unit': 'minute',
        'win': win,
        'arr': lam * win,
        'dep': lam * (1.0 - p_loss) * win,
        'blk': lam * p_loss * win,
        'dep_rate': dep_rate,
        'lam_eff': lam * (1.0 - p_loss) * 60.0,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'per_seed_p_loss': per_ploss,
        'per_seed_p_wait': per_pwait,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
