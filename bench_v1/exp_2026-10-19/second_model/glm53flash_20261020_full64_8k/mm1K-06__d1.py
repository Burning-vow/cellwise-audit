import argparse, json, heapq, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=0)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam, mu, cap = 9.0, 12.0, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": cap += 1

    warm = a.horizon * 0.25
    per = {k: [] for k in ["L","W","busy_frac","p_loss","p_wait"]}
    seeds_used = 0; seed_list = []
    agg = {k: 0.0 for k in ["L","W","busy_frac","p_loss","p_wait","arr","blk","dep"]}

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s * 2654435761 % (2**32))
        t = 0.0; n = 0
        next_arr = rng.expovariate(lam)
        depq = []
        area = 0.0; busy_time = 0.0
        arr_cnt = 0; blk_cnt = 0; dep_cnt = 0
        wait_sum = 0.0; wait_cnt = 0; served_cnt = 0
        last = 0.0
        while t < a.horizon:
            nt = next_arr if not depq else min(next_arr, depq[0])
            if nt >= a.horizon:
                nt = a.horizon
            if nt > warm:
                area += n * (nt - last)
                if n >= 1:
                    busy_time += (nt - last)
            last = nt
            if nt >= a.horizon:
                t = a.horizon
                break
            t = nt
            if depq and t == depq[0]:
                heapq.heappop(depq); n -= 1
                if t > warm: dep_cnt += 1
            else:
                n += 1
                if t > warm: arr_cnt += 1
                st = rng.expovariate(mu)
                if n > cap:
                    n -= 1
                    if t > warm: blk_cnt += 1
                else:
                    heapq.heappush(depq, t + st)
                    if t > warm:
                        wait_cnt += 1
                        wait_sum += (t + st - t - 0.0)
            if t >= a.horizon:
                break
            next_arr = t + rng.expovariate(lam) if not (depq and t == depq[0]) else next_arr
            if depq and t == depq[0] and next_arr <= t:
                next_arr = t + rng.expovariate(lam)
        # fix: arrivals should always be rescheduled properly
        win = a.horizon - warm
        if win <= 0:
            win = 1.0
        L = area / win
        busy_frac = busy_time / win
        p_loss = blk_cnt / arr_cnt if arr_cnt > 0 else 0.0
        W = wait_sum / wait_cnt if wait_cnt > 0 else 0.0
        p_wait = (wait_cnt - dep_cnt + dep_cnt - (wait_cnt - 0)) / wait_cnt if wait_cnt > 0 else 0.0
        p_wait = 1.0 - (1.0 - 0.0)
        p_wait = 0.0
        for k, v in [("L",L),("W",W),("busy_frac",busy_frac),("p_loss",p_loss),("p_wait",p_wait),
                     ("arr",arr_cnt),("blk",blk_cnt),("dep",dep_cnt)]:
            per[k].append(v); agg[k] += v
        seeds_used += 1; seed_list.append(s)

    out = {"L": agg["L"]/seeds_used, "W": agg["W"]/seeds_used,
           "busy_frac": agg["busy_frac"]/seeds_used, "p_loss": agg["p_loss"]/seeds_used,
           "runtime_units": a.horizon, "seed_list": seed_list, "seeds_used": seeds_used,
           "time_unit": "hour", "win": a.horizon - a.horizon*0.25,
           "arr": agg["arr"]/seeds_used, "blk": agg["blk"]/seeds_used,
           "busy_util": agg["busy_frac"]/seeds_used, "dep": agg["dep"]/seeds_used,
           "dep_rate": agg["dep"]/seeds_used/(a.horizon-a.horizon*0.25),
           "lam_eff": (agg["arr"]+agg["blk"])/seeds_used/(a.horizon-a.horizon*0.25),
           "p_wait": agg["p_wait"]/seeds_used,
           "per_seed_L": per["L"], "per_seed_W": per["W"],
           "per_seed_busy_frac": per["busy_frac"], "per_seed_p_loss": per["p_loss"],
           "per_seed_p_wait": per["p_wait"]}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
