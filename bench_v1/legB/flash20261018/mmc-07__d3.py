import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 12.0
    c = 3
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 4

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_soj = 0.0
    tot_dep_win = 0.0
    tot_pw_num = 0.0
    tot_pw_den = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        areaN = 0.0
        areaB = 0.0
        wait_sum = 0.0
        soj_sum = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        pw_num = 0.0
        pw_den = 0.0
        last = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            if not queue and not servers:
                nxt = next_arr
            elif not queue:
                nxt = min(next_arr, servers[0])
            elif not servers:
                nxt = next_arr
            else:
                nxt = min(next_arr, servers[0])
            if nxt > H:
                dt = H - t
                areaN += n * dt
                areaB += busy * dt
                t = H
                break
            dt = nxt - t
            areaN += n * dt
            areaB += busy * dt
            t = nxt
            if t >= next_arr:
                svc = rng.expovariate(mu)
                n += 1
                if t >= warm:
                    arr_w += 1
                    pw_den += 1.0
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    servers.sort()
                    if t >= warm:
                        soj_sum += svc
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        pw_num += 1.0
                next_arr = t + rng.expovariate(lam)
            else:
                servers.pop(0)
                busy -= 1
                if t >= warm:
                    dep_w += 1
                if queue:
                    at, svc = queue.pop(0)
                    if t >= warm:
                        wait_sum += (t - at)
                        soj_sum += svc
                    servers.append(t + svc)
                    servers.sort()
                    busy += 1
        win = H - warm
        win_total += win
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_soj += soj_sum
        tot_dep_win += dep_w
        tot_pw_num += pw_num
        tot_pw_den += pw_den
        Ls = areaN / win if win > 0 else 0.0
        Ws = (wait_sum + soj_sum) / dep_w if dep_w > 0 else 0.0
        bfs = areaB / (c * win) if win > 0 else 0.0
        pls = blk_w / arr_w if arr_w > 0 else 0.0
        pws = pw_num / pw_den if pw_den > 0 else 0.0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bfs)
        per_pl.append(pls)
        per_pw.append(pws)

    L = tot_areaN / win_total if win_total > 0 else 0.0
    W = (tot_wait + tot_soj) / tot_dep if tot_dep > 0 else 0.0
    busy_frac = tot_areaB / (c * win_total) if win_total > 0 else 0.0
    p_wait = tot_pw_num / tot_pw_den if tot_pw_den > 0 else 0.0
    arr = tot_arr / len(seeds)
    dep = tot_dep / len(seeds)
    blk = tot_blk / len(seeds)
    dep_rate = tot_dep_win / win_total if win_total > 0 else 0.0
    p_loss = blk / arr if arr > 0 else 0.0
    lam_eff = dep_rate
    busy_util = busy_frac
    busy_occupied = busy_frac

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': win_total / len(seeds),
        'arr': arr, 'blk': blk, 'busy_util': busy_util,
        'busy_occupied': busy_occupied, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': p_loss,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
