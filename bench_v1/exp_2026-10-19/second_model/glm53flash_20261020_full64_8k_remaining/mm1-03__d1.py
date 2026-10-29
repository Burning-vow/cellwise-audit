import argparse, json, random, math, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=4800.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); horizon = float(a.horizon); s0 = int(a.seed_start)
    lam, mu = 6.0/60.0, 1.0/6.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": mu *= 1.05
    warm = horizon * 0.25
    def expv(rng, rate):
        return -math.log(1.0 - rng.random()) / rate
    per_L=[]; per_W=[]; per_bf=[]; per_pl=[]; per_pw=[]; seed_list=[]
    tot_arr=tot_dep=tot_blk=0.0
    for k in range(n_seeds):
        seed = s0 + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        next_arr = expv(rng, lam)
        nxt_dep = math.inf
        n = 0
        queue = []
        area_N = 0.0; area_busy = 0.0; busy_min = 0.0
        wait_sum = 0.0; nw = 0; nwaited = 0
        arr_c = 0; dep_c = 0; blk_c = 0
        last = 0.0
        while t < horizon:
            t_prev = t
            t = min(next_arr, nxt_dep, horizon)
            if t > warm and n >= 0:
                dt = t - t_prev
                area_N += n * dt
                if n >= 1:
                    area_busy += dt
                    busy_min += dt
            if t >= horizon:
                break
            if next_arr <= nxt_dep:
                t = next_arr
                st = expv(rng, mu)
                arr_c += 1
                if n == 0:
                    n = 1
                    nxt_dep = t + st
                    nwaited += 0
                    waits = 0.0
                    svc_start = t
                    served = (t, st, t)
                    heapq.heappush(queue, (t, st, 0.0))
                else:
                    heapq.heappush(queue, (t, st, None))
                n += 0
                next_arr = t + expv(rng, lam)
            else:
                t = nxt_dep
                dep_c += 1
                n -= 1
                if queue:
                    item = heapq.heappop(queue)
                    at, st, flag = item
                    if flag is None:
                        pass
                if n > 0:
                    pass
                if queue:
                    pass
            if False:
                pass
        per_L.append(area_N/(horizon-warm))
        per_bf.append(area_busy/(horizon-warm))
        per_pl.append(blk_c/max(arr_c,1))
        per_W.append(wait_sum/nw if nw else 0.0)
        per_pw.append(nwaited/max(arr_c,1))
        tot_arr += arr_c; tot_dep += dep_c; tot_blk += blk_c
    seeds_used = n_seeds
    win = horizon - warm
    L = sum(per_L)/seeds_used
    W = sum(per_W)/seeds_used
    busy_frac = sum(per_bf)/seeds_used
    p_wait = sum(per_pw)/seeds_used
    out = {
        "L": L, "W": W, "busy_frac": busy_frac, "p_wait": p_wait,
        "runtime_units": horizon, "seed_list": seed_list, "seeds_used": seeds_used,
        "time_unit": "minute", "win": win,
        "arr": tot_arr/seeds_used, "blk": tot_blk/seeds_used,
        "busy_util": busy_frac, "dep": tot_dep/seeds_used,
        "dep_rate": tot_dep/seeds_used/(win/60.0),
        "lam_eff": tot_arr/seeds_used/(win/60.0),
        "p_loss": tot_blk/seeds_used/max(tot_arr,1),
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
