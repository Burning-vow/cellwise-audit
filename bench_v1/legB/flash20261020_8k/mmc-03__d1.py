import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    c = 2
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_soj = 0.0
    tot_dep_t = 0.0
    tot_pw_num = 0.0
    tot_pw_den = 0.0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = [None] * c
        arr_times = []
        areaN = areaB = 0.0
        wait_sum = soj_sum = 0.0
        dep_cnt = 0
        blk_cnt = 0
        arr_cnt = 0
        pw_num = pw_den = 0.0
        dep_t_sum = 0.0
        last = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            cand = [next_arr]
            for sv in servers:
                if sv is not None:
                    cand.append(sv[0])
            tn = min(cand)
            if tn > H:
                dt = H - t
                if t >= warm:
                    areaN += n * dt
                    areaB += busy * dt
                t = H
                break
            dt = tn - t
            if t >= warm:
                areaN += n * dt
                areaB += busy * dt
            t = tn
            if next_arr <= t + 1e-12 and abs(next_arr - t) < 1e-9:
                arr_cnt += 1
                if t >= warm:
                    pw_den += 1
                    if n >= c:
                        pw_num += 1
                if n >= c:
                    blk_cnt += 1
                else:
                    svc = rng.expovariate(mu)
                    if busy < c:
                        servers[busy] = (t + svc, t, svc)
                        busy += 1
                    else:
                        queue.append((t, svc))
                n += 1
                next_arr = t + rng.expovariate(lam)
            for i in range(c):
                sv = servers[i]
                if sv is not None and abs(sv[0] - t) < 1e-9:
                    servers[i] = None
                    busy -= 1
                    n -= 1
                    dep_cnt += 1
                    if t >= warm:
                        soj_sum += (t - sv[1])
                        dep_t_sum += t
                    if queue:
                        at, svc = queue.pop(0)
                        servers[i] = (t + svc, at, svc)
                        busy += 1
                        n += 1
                        if t >= warm:
                            wait_sum += (t - at)
        win = H - warm
        win_total += win
        tot_arr += arr_cnt
        tot_dep += dep_cnt
        tot_blk += blk_cnt
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_soj += soj_sum
        tot_dep_t += dep_t_sum
        tot_pw_num += pw_num
        tot_pw_den += pw_den
        Ls = areaN / win if win > 0 else 0.0
        Ws = (wait_sum + soj_sum) / dep_cnt if dep_cnt > 0 else 0.0
        bfs = areaB / (c * win) if win > 0 else 0.0
        pls = blk_cnt / arr_cnt if arr_cnt > 0 else 0.0
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
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    dep_rate = tot_dep / (win_total / 60.0) if win_total > 0 else 0.0
    lam_eff = tot_arr / (win_total / 60.0) if win_total > 0 else 0.0
    busy_util = busy_frac
    busy_occupied = busy_frac

    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': 'minute', 'seed_list': seeds, 'seeds_used': len(seeds),
        'time_unit': 'minute', 'win': win_total / len(seeds) if seeds else 0.0,
        'arr': tot_arr / len(seeds) if seeds else 0.0,
        'dep': tot_dep / len(seeds) if seeds else 0.0,
        'blk': tot_blk / len(seeds) if seeds else 0.0,
        'busy_util': busy_util, 'busy_occupied': busy_occupied,
        'dep_rate': dep_rate, 'lam_eff': lam_eff, 'p_loss': p_loss,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
