import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    c = 1
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_areaN = tot_areaB = 0.0
    tot_win = 0.0
    tot_wait = 0.0
    tot_wait_n = 0
    tot_dep_n = 0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        # event list: (time, type, payload)
        events = []
        # schedule first arrival
        events.append((next_arr, 'arr', None))
        # service completions heap
        import heapq
        comp = []
        areaN = 0.0
        areaB = 0.0
        last_t = 0.0
        win_start = warm
        win_areaN = 0.0
        win_areaB = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait = 0.0
        win_wait_n = 0
        win_dep_n = 0
        # we integrate area over [0,H]; accumulate only in window
        while True:
            # next event time
            ta = events[0][0] if events else float('inf')
            tc = comp[0][0] if comp else float('inf')
            tn = min(ta, tc)
            if tn > H:
                # integrate to H
                dt = H - last_t
                if last_t < H:
                    if last_t >= win_start:
                        win_areaN += n * dt
                        win_areaB += (1 if busy > 0 else 0) * dt
                    elif H > win_start:
                        # partial
                        seg = H - win_start
                        win_areaN += n * seg
                        win_areaB += (1 if busy > 0 else 0) * seg
                last_t = H
                break
            dt = tn - last_t
            if dt > 0:
                if last_t >= win_start:
                    win_areaN += n * dt
                    win_areaB += (1 if busy > 0 else 0) * dt
                elif tn > win_start:
                    seg = tn - win_start
                    win_areaN += n * seg
                    win_areaB += (1 if busy > 0 else 0) * seg
            last_t = tn
            if ta <= tc:
                events.pop(0)
                # arrival
                n += 1
                if tn >= win_start:
                    win_arr += 1
                # draw service time now
                st = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    heapq.heappush(comp, (tn + st, st))
                else:
                    # loss (no queue, c=1 blocking)
                    n -= 1
                    if tn >= win_start:
                        win_blk += 1
                # schedule next arrival
                na = tn + rng.expovariate(lam)
                events.append((na, 'arr', None))
            else:
                heapq.heappop(comp)
                busy -= 1
                n -= 1
                if tn >= win_start:
                    win_dep += 1
                    win_dep_n += 1
        win_len = H - win_start
        Ls = win_areaN / win_len if win_len > 0 else 0.0
        Bs = win_areaB / win_len if win_len > 0 else 0.0
        # W = L / lambda_eff ; lambda_eff = dep_rate
        dep_rate = win_dep / win_len if win_len > 0 else 0.0
        Ws = Ls / dep_rate if dep_rate > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        pw = 0.0  # no queue, c=1 blocking -> p_wait = 0
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(Bs)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_areaN += win_areaN
        tot_areaB += win_areaB
        tot_win += win_len

    nseeds = len(seeds)
    L = tot_areaN / tot_win if tot_win > 0 else 0.0
    busy_frac = tot_areaB / tot_win if tot_win > 0 else 0.0
    dep_rate = tot_dep / tot_win if tot_win > 0 else 0.0
    W = L / dep_rate if dep_rate > 0 else 0.0
    arr_avg = tot_arr / nseeds
    dep_avg = tot_dep / nseeds
    blk_avg = tot_blk / nseeds
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = 0.0
    lam_eff = dep_rate

    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "busy_util": busy_frac,
        "busy_occupied": busy_frac,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": nseeds,
        "time_unit": "minute",
        "win": tot_win / nseeds if nseeds > 0 else 0.0,
        "arr": arr_avg,
        "dep": dep_avg,
        "blk": blk_avg,
        "dep_rate": dep_rate,
        "lam_eff": lam_eff,
        "p_loss": p_loss,
        "p_wait": p_wait,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
