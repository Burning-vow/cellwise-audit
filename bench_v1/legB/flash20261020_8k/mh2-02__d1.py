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
    cv = 1.5
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mean_s /= 1.2
    elif a.pert == 'c_up':
        cv *= 1.2

    var_s = (cv * mean_s) ** 2
    p2 = 0.5 * (1.0 + math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2))))
    p2 = min(max(p2, 0.0), 1.0)
    m1 = mean_s * (1.0 - math.sqrt(max(0.0, (var_s - mean_s**2) / (var_s + mean_s**2)))) if var_s > mean_s**2 else mean_s
    m1 = max(m1, 1e-9)
    m2 = max(2.0 * mean_s - m1, 1e-9)

    H = a.horizon
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait_n = tot_wait_sum = 0.0
    tot_win = 0.0

    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_times = []
        while True:
            t += rng.expovariate(lam)
            if t > H:
                break
            arr_times.append(t)
        events = []
        for at in arr_times:
            u = rng.random()
            s = m1 if u < p2 else m2
            s = rng.expovariate(1.0 / s)
            events.append((at, s))
        events.sort()
        idx = 0
        area = 0.0
        busy_time = 0.0
        last = 0.0
        win_area = 0.0
        win_busy = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait_n = 0
        win_wait_sum = 0.0
        cur = 0.0
        while idx < len(events) or busy:
            if busy:
                nxt = min(cur + rem, events[idx][0] if idx < len(events) else float('inf'))
            else:
                nxt = events[idx][0] if idx < len(events) else float('inf')
            if nxt == float('inf'):
                break
            dt = nxt - cur
            if dt > 0:
                if cur >= warm:
                    end = min(nxt, H)
                    if end > cur:
                        win_area += n * (end - cur)
                        if busy:
                            win_busy += (end - cur)
                if busy:
                    rem -= dt
            cur = nxt
            if busy and rem <= 1e-12:
                busy = False
                n -= 1
                if cur >= warm and cur <= H:
                    win_dep += 1
            if idx < len(events) and abs(events[idx][0] - cur) < 1e-12:
                at, s = events[idx]
                idx += 1
                if cur >= warm and cur <= H:
                    win_arr += 1
                if not busy:
                    busy = True
                    n += 1
                    rem = s
                    if cur >= warm and cur <= H:
                        win_wait_n += 1
                        win_wait_sum += 0.0
                else:
                    n += 1
                    if cur >= warm and cur <= H:
                        win_blk += 1
                        win_wait_n += 1
                        win_wait_sum += 0.0
            if cur >= H:
                break
        win = max(H - warm, 1e-9)
        L = win_area / win
        W = L / lam if lam > 0 else 0.0
        bf = win_busy / win
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        pw = win_wait_n / win_arr if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += win_area
        tot_busy += win_busy
        tot_wait_n += win_wait_n
        tot_wait_sum += win_wait_sum
        tot_win += win

    ns = len(seeds)
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = L / lam if lam > 0 else 0.0
    busy_frac = tot_busy / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / (tot_win / ns) if tot_win > 0 else 0.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = tot_wait_n / tot_arr if tot_arr > 0 else 0.0
    lam_eff = dep_rate

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'hour', 'win': tot_win / ns,
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': p_loss, 'p_wait': p_wait,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
