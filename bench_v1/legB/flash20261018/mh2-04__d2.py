import json, math, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 5.0
    mean_s = 0.1
    cv = 2.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    H = float(a.horizon)
    warm = 0.25 * H
    n = a.seeds
    seeds = [a.seed_start + i for i in range(n)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_area = 0.0
    tot_waiters_area = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        busy = False
        rem = 0.0
        queue = []
        area = 0.0
        busy_area = 0.0
        wait_area = 0.0
        waiters_area = 0.0
        arr = dep = blk = 0
        waited = 0
        wsum = 0.0
        last = 0.0
        win_start = warm
        win_area = 0.0
        win_busy = 0.0
        win_wait_area = 0.0
        win_waiters = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_waited = 0
        win_wsum = 0.0
        t_next = rng.expovariate(lam)
        while t < H:
            if not busy and queue:
                cust = queue.pop(0)
                busy = True
                rem = cust[1]
                w = t - cust[0]
                wsum += w
                waited += 1
                if t >= win_start:
                    win_wsum += w
                    win_waited += 1
            if busy:
                dt = min(rem, t_next - t if t_next > t else 0.0, H - t)
            else:
                dt = min(t_next - t, H - t)
            if dt < 0:
                dt = 0.0
            if t >= win_start:
                win_area += (1 if busy else 0) * dt
                win_busy += (1 if busy else 0) * dt
                win_waiters += len(queue) * dt
            area += (1 if busy else 0) * dt
            busy_area += (1 if busy else 0) * dt
            waiters_area += len(queue) * dt
            t += dt
            if busy:
                rem -= dt
                if rem <= 1e-12:
                    busy = False
                    dep += 1
                    if t >= win_start:
                        win_dep += 1
            if t >= t_next - 1e-12 and t_next <= H:
                s = 0.0
                if cv == 1.0:
                    s = rng.expovariate(1.0 / mean_s)
                else:
                    p = 0.5 * (1.0 + math.sqrt((cv * cv - 1.0) / (cv * cv + 1.0)))
                    m1 = mean_s * p
                    m2 = mean_s * (1.0 - p)
                    if rng.random() < p:
                        s = rng.expovariate(1.0 / m1)
                    else:
                        s = rng.expovariate(1.0 / m2)
                arr += 1
                if t >= win_start:
                    win_arr += 1
                if busy:
                    queue.append((t, s))
                else:
                    busy = True
                    rem = s
                t_next = t + rng.expovariate(lam)
        win_len = max(H - win_start, 1e-9)
        Ls = win_area / win_len
        Ws = (win_wsum / win_waited) if win_waited > 0 else 0.0
        bfs = win_busy / win_len
        pls = win_blk / win_arr if win_arr > 0 else 0.0
        pws = win_waited / win_arr if win_arr > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += win_area
        tot_busy += win_busy
        tot_wait_area += win_wsum
        tot_waiters_area += win_waiters
        tot_win += win_len

    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = (tot_wait_area / sum(1 for _ in per_W)) if False else 0.0
    total_waited = 0
    total_wsum = 0.0
    for sd in seeds:
        pass
    W = sum(per_W) / len(per_W) if per_W else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    busy_util = busy_frac
    busy_occupied = busy_frac
    arr_avg = tot_arr / n
    dep_avg = tot_dep / n
    blk_avg = tot_blk / n
    dep_rate = (tot_dep / n) / (tot_win / n) if tot_win > 0 else 0.0
    lam_eff = (tot_arr / n) / (tot_win / n) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = sum(per_pw) / len(per_pw) if per_pw else 0.0

    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_util,
        'busy_occupied': busy_occupied,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': n,
        'time_unit': 'hour',
        'win': tot_win / n if n > 0 else 0.0,
        'arr': arr_avg,
        'dep': dep_avg,
        'blk': blk_avg,
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
