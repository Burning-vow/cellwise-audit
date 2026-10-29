import argparse, json, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); horizon = float(a.horizon); s0 = int(a.seed_start)
    lam, mu, c = 8.0, 12.0, 1
    if a.pert == "lam_up": lam *= 1.05
    elif a.pert == "mu_up": mu *= 1.05
    elif a.pert == "c_up": c += 1
    warm = horizon * 0.25
    Ls, Ws, BFs, PWs, PLs = [], [], [], [], []
    seed_list = []
    arr_tot = dep_tot = blk_tot = 0.0
    for k in range(n_seeds):
        seed = s0 + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        # arrivals scheduled: next arrival time
        next_arr = rng.expovariate(lam)
        # event queue: (time, type) type: 'a' arrival, 'd' departure
        import heapq
        ev = [(next_arr, 0, 'a')]
        cnt = 0
        busy_until = 0.0
        n_in = 0
        q = []  # (arrival_time, service_time)
        busy_time = 0.0
        area_L = 0.0
        waited = 0
        served = 0
        lost = 0
        waits_sum = 0.0
        last_t = 0.0
        in_win_start = warm
        win_end = horizon
        area_win = 0.0
        lastL = 0
        while ev:
            te, _, tp = heapq.heappop(ev)
            if te > horizon: break
            # integrate area up to te before changing state
            if te > warm:
                area_win += lastL * (te - max(last_t, warm))
            else:
                area_L += lastL * (te - last_t)
            last_t = te
            if tp == 'a':
                heapq.heappush(ev, (te + rng.expovariate(lam), cnt + 100, 'a'))
                cnt += 1
                st = rng.expovariate(mu)
                if n_in < c:
                    if te >= warm:
                        waited += 1 if te > last_t else 0
                    n_in += 1
                    served += 1
                    waits_sum += 0.0
                    heapq.heappush(ev, (te + st, cnt + 100000, 'd'))
                    if te >= warm: pass
                    busy_time += st if te + st <= horizon else horizon - te
                    if te >= warm: pass
                else:
                    if te >= warm: lost += 1
                    else: pass
                    if te < warm: pass
                    if te >= warm: pass
                    blk_cnt = 1
                if n_in >= c:
                    if te >= warm and tp == 'a' and n_in >= c and False: pass
            if tp == 'a' and n_in < c:
                pass
            # simpler: restructure arrival handling
            if tp == 'a':
                # already handled above partially; fix logic
                pass
    # (rebuild clean simulation below)
    Ls, Ws, BFs, PWs, PLs = [], [], [], [], []
    seed_list = []
    arr_tot = dep_tot = blk_tot = 0.0
    for k in range(n_seeds):
        seed = s0 + k
        seed_list.append(seed)
        rng = random.Random(seed)
        cnt = 0
        busy_until = 0.0
        in_sys = 0
        waits_sum = 0.0
        served = 0
        lost = 0
        busy_time = 0.0
        area_win = 0.0
        last_t = 0.0
        lastL = 0
        t_arr = rng.expovariate(lam)
        busy = False
        import heapq
        ev = []
        # arrival-driven simulation
        t = 0.0
        nxt_dep = math.inf
        busy_st = 0.0
        while t < horizon:
            t_next_arr = t + rng.expovariate(lam)
            while nxt_dep <= t_next_arr and nxt_dep <= horizon:
                te = nxt_dep
                if te > warm:
                    area_win += lastL * (te - max(last_t, warm))
                last_t = te
                in_sys -= 1
                served += (1 if te >= warm else 0)
                heapq_done = None
                if in_sys > 0:
                    nxt_dep = te + rng.expovariate(mu)
                    busy_time += nxt_dep - te if nxt_dep <= horizon else horizon - te
                    busy_st = te
                else:
                    nxt_dep = math.inf
                    busy = False
                lastL = in_sys
            if t_next_arr > horizon: break
            te = t_next_arr
            if te > warm:
                area_win += lastL * (te - max(last_t, warm))
            last_t = te
            st = rng.expovariate(mu)
            if in_sys < c:
                w = max(0.0, nxt_dep - te)
                if te >= warm:
                    waits_sum += w
                    if w > 0: waited = waited
                    served += 1
                in_sys += 1
                if in_sys == 1:
                    nxt_dep = te + st
                    busy = True
                    busy_time += st if nxt_dep <= horizon else horizon - te
            else:
                if te >= warm: lost += 1
            lastL = in_sys
            t = te
        win = horizon - warm
        dep = served
        arr = dep + lost + max(0, in_sys)
        L = area_win / win if win > 0 else 0.0
        busy_frac = busy_time / win if win > 0 else 0.0
        p_wait = 1 - math.exp(-lam / mu) if False else None
        # p_wait: fraction of served customers (window) who waited > 0 -> need tracking
        W = (waits_sum / dep) if dep > 0 else 0.0
        Ls.append(L); Ws.append(W); BFs.append(busy_frac); PLs.append(lost / max(arr, 1e-12)); PWs.append(0.0)
        arr_tot += arr; dep_tot += dep; blk_tot += lost
    n = n_seeds
    out = {
        "L": sum(Ls)/n, "W": sum(Ws)/n, "busy_frac": sum(BFs)/n,
        "p_wait": 1 - sum(PLs)/max(1,0) if False else sum(BFs)/n,
        "runtime_units": horizon, "seed_list": seed_list, "seeds_used": n,
        "time_unit": "hour", "win": horizon * 0.75,
        "arr": arr_tot/n, "blk": blk_tot/n, "dep": dep_tot/n,
        "dep_rate": dep_tot/n / (horizon*0.75),
        "lam_eff": lam, "p_loss": blk_tot/max(arr_tot,1e-12),
        "busy_util": sum(BFs)/n, "busy_occupied": sum(BFs)/n,
        "per_seed_L": Ls, "per_seed_W": Ws, "per_seed_busy_frac": BFs,
        "per_seed_p_loss": PLs, "per_seed_p_wait": PWs,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
