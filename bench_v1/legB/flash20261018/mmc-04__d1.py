import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 10.0
    mu = 6.0
    c = 2
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 3

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_wait = tot_soj = 0.0
    tot_dep_cnt = 0
    tot_arr_cnt = 0
    tot_wait_cnt = 0
    tot_waiters = 0
    win_total = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        next_arr = rng.expovariate(lam)
        areaN = areaB = 0.0
        wait_sum = soj_sum = 0.0
        dep_cnt = arr_cnt = blk_cnt = wait_cnt = waiters = 0
        last = 0.0
        while t < H:
            if next_arr <= t:
                dt = next_arr - last
                if t > warm:
                    areaN += n * dt
                    areaB += busy * dt
                last = next_arr
                t = next_arr
                arr_cnt += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    n += 1
                    dep_t = t + svc
                    queue.append((dep_t, t, svc))
                else:
                    n += 1
                    queue.append((None, t, svc))
                next_arr = t + rng.expovariate(lam)
            else:
                if not queue:
                    dt = next_arr - last
                    if t > warm:
                        areaN += n * dt
                        areaB += busy * dt
                    last = next_arr
                    t = next_arr
                    continue
                # find earliest completion
                best = None
                bi = -1
                for i, q in enumerate(queue):
                    if q[0] is not None and (best is None or q[0] < best):
                        best = q[0]
                        bi = i
                if best is None:
                    dt = next_arr - last
                    if t > warm:
                        areaN += n * dt
                        areaB += busy * dt
                    last = next_arr
                    t = next_arr
                    continue
                if best < next_arr:
                    dt = best - last
                    if best > warm:
                        areaN += n * dt
                        areaB += busy * dt
                    last = best
                    t = best
                    dep_t, at, svc = queue.pop(bi)
                    busy -= 1
                    n -= 1
                    dep_cnt += 1
                    if t > warm:
                        soj_sum += (t - at)
                    # start next waiting
                    for i, q in enumerate(queue):
                        if q[0] is None:
                            nd = t + q[2]
                            queue[i] = (nd, q[1], q[2])
                            busy += 1
                            if t > warm:
                                wait_sum += (t - q[1])
                                wait_cnt += 1
                            break
                else:
                    dt = next_arr - last
                    if next_arr > warm:
                        areaN += n * dt
                        areaB += busy * dt
                    last = next_arr
                    t = next_arr
        # final integration to H
        if H > last and H > warm:
            areaN += n * (H - last)
            areaB += busy * (H - last)
        win = H - warm
        win_total += win
        L = areaN / win if win > 0 else 0.0
        bf = areaB / (c * win) if win > 0 else 0.0
        W = soj_sum / dep_cnt if dep_cnt > 0 else 0.0
        pw = wait_cnt / arr_cnt if arr_cnt > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        tot_areaN += areaN
        tot_areaB += areaB
        tot_wait += wait_sum
        tot_soj += soj_sum
        tot_dep_cnt += dep_cnt
        tot_arr_cnt += arr_cnt
        tot_wait_cnt += wait_cnt
        tot_arr += arr_cnt
        tot_dep += dep_cnt
        tot_blk += blk_cnt

    nseeds = len(seeds)
    L = tot_areaN / win_total if win_total > 0 else 0.0
    busy_frac = tot_areaB / (c * win_total) if win_total > 0 else 0.0
    W = tot_soj / tot_dep_cnt if tot_dep_cnt > 0 else 0.0
    p_wait = tot_wait_cnt / tot_arr_cnt if tot_arr_cnt > 0 else 0.0
    arr = tot_arr / nseeds
    dep = tot_dep / nseeds
    blk = tot_blk / nseeds
    dep_rate = dep / (win_total / nseeds) if win_total > 0 else 0.0
    lam_eff = arr / (win_total / nseeds) if win_total > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': busy_frac, 'p_wait': p_wait,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': nseeds,
        'time_unit': 'hour', 'win': win_total / nseeds,
        'arr': arr, 'blk': blk, 'busy_util': busy_frac,
        'busy_occupied': busy_frac, 'dep': dep, 'dep_rate': dep_rate,
        'lam_eff': lam_eff, 'p_loss': 0.0,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
