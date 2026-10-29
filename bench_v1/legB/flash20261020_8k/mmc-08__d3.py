import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 10.0
    c = 3
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 4

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_served = 0.0
    tot_arrived = tot_waiters = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        next_arr = rng.expovariate(lam)
        areaN = areaB = 0.0
        wait_sum = 0.0
        served = 0
        arrived = 0
        waiters = 0
        lost = 0
        last_t = 0.0
        win_areaN = win_areaB = 0.0
        win_wait = win_served = 0.0
        win_arr = win_waiters = win_lost = 0.0
        win_start = warm
        win_len = H - warm

        while True:
            # next event time
            t_dep = servers[0][0] if servers else float('inf')
            t_arr = next_arr
            if t_dep < t_arr:
                t_next = t_dep
            else:
                t_next = t_arr
            if t_next > H:
                # integrate to H
                dt = H - last_t
                if last_t >= win_start or t_next > win_start:
                    a0 = max(last_t, win_start)
                    dt2 = H - a0
                    if dt2 > 0:
                        win_areaN += n * dt2
                        win_areaB += busy * dt2
                break
            dt = t_next - last_t
            if dt > 0:
                a0 = max(last_t, win_start)
                dt2 = t_next - a0
                if dt2 > 0:
                    win_areaN += n * dt2
                    win_areaB += busy * dt2
            last_t = t_next
            t = t_next

            if t_dep <= t_arr:
                # departure
                servers.sort()
                _, sid = servers.pop(0)
                busy -= 1
                n -= 1
                if t >= win_start:
                    win_served += 1
                if queue:
                    qt, st, cust = queue.pop(0)
                    start = t
                    wait = start - qt
                    if t >= win_start:
                        win_wait += wait
                    servers.append((t + st, cust))
                    servers.sort()
                    busy += 1
                    n += 1
            else:
                # arrival
                st = rng.expovariate(mu)
                arrived += 1
                if t >= win_start:
                    win_arr += 1
                if busy < c:
                    servers.append((t + st, arrived))
                    servers.sort()
                    busy += 1
                    n += 1
                else:
                    queue.append((t, st, arrived))
                    n += 1
                    if t >= win_start:
                        win_waiters += 1
                next_arr = t + rng.expovariate(lam)

        per_L.append(win_areaN / win_len if win_len > 0 else 0.0)
        per_W.append((win_wait + win_served * (1.0/mu)) / win_served if win_served > 0 else 0.0)
        per_bf.append(win_areaB / win_len / c if win_len > 0 else 0.0)
        per_pl.append(0.0)
        per_pw.append(win_waiters / win_arr if win_arr > 0 else 0.0)
        tot_areaN += win_areaN
        tot_areaB += win_areaB
        tot_arr += win_arr
        tot_dep += win_served
        tot_blk += win_lost
        tot_wait += win_wait
        tot_served += win_served
        tot_arrived += win_arr
        tot_waiters += win_waiters
        win_total += win_len

    ns = len(seeds)
    L = tot_areaN / win_total if win_total > 0 else 0.0
    W = (tot_wait + tot_served / mu) / tot_served if tot_served > 0 else 0.0
    busy_frac = tot_areaB / win_total / c if win_total > 0 else 0.0
    p_wait = tot_waiters / tot_arrived if tot_arrived > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / (win_total / ns) if win_total > 0 else 0.0

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': 'minute', 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win_total / ns if ns > 0 else 0.0,
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam, 'p_loss': 0.0,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
