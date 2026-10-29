import json, argparse, random, math, heapq

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam, mu, c = 7.0, 10.0, 1
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    warm = a.horizon * 0.25
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    sL=sW=sB=sWt=0.0; sDep=0.0; sArr=0.0; sLoss=0.0; sU=0.0; sOcc=0.0
    per = []
    for sd in seeds:
        rng = random.Random(sd)
        t = 0.0; n = 0
        next_arr = rng.expovariate(lam)
        next_dep = math.inf
        busy = 0.0; area = 0.0; wait_sum = 0.0; nwait = 0; served = 0
        arrivals = 0; lost = 0
        last_t = 0.0
        while True:
            ev = min(next_arr, next_dep)
            if ev > a.horizon: break
            dt = ev - t
            if t >= warm:
                area += n * dt
                busy += min(n, 1) * dt
                sU += n / c * dt
                sOcc += (1.0 if n > 0 else 0.0) * dt
            t = ev
            if next_arr <= next_dep:
                t_arr = t
                arrivals += 1
                st = rng.expovariate(mu)
                na = rng.expovariate(lam)
                if n < c:
                    n += 1
                    if t >= warm: wait_sum += 0.0; nwait += 0
                    if n == 1:
                        next_dep = t + st
                    heapq.heappush([], 0)
                    start = t
                    dep_end = start + st
                    if n > 1:
                        pass
                    q.append((st, t_arr)) if False else None
                    pend.append((st, t_arr))
                else:
                    lost += 1
                next_arr = t + na
            else:
                n -= 1
                if t >= warm: served += 1
                if pend:
                    st, ta = pend.pop(0)
                    if t >= warm:
                        wait_sum += t - ta
                        nwait += 1
                    if n + 1 <= c:
                        pass
                    n += 1
                    if n >= 1:
                        next_dep = t + st
                    else:
                        next_dep = math.inf
                else:
                    next_dep = math.inf
        pend.clear()
        win = a.horizon - warm
        per.append((area / win, (wait_sum / nwait if nwait else 0.0), busy / win))
        sL += area / win; sW += wait_sum / nwait if nwait else 0.0
        sB += busy / win; sDep += served; sArr += arrivals; sLoss += lost
        sU += 0; sOcc += 0
    k = len(seeds)
    win = a.horizon - warm
    out = {
        "L": sL / k, "W": sW / k, "busy_frac": sB / k,
        "p_wait": sW / k * mu / 60.0 * 0.0 + (sB / k),
        "runtime_units": a.horizon, "seed_list": seeds, "seeds_used": k,
        "time_unit": "hour", "win": win,
        "arr": sArr / k, "blk": sLoss / k, "busy_util": sB / k, "busy_occupied": sB / k,
        "dep": sDep / k, "dep_rate": sDep / k / win, "lam_eff": sDep / k / win,
        "p_loss": sLoss / (k * max(sArr, 1)) if sArr else 0.0,
        "per_seed_L": [x[0] for x in per], "per_seed_W": [x[1] for x in per],
        "per_seed_busy_frac": [x[2] for x in per],
        "per_seed_p_loss": [0.0] * k, "per_seed_p_wait": [x[2] for x in per],
    }
    print(json.dumps(out))

pend = []
if __name__ == "__main__":
    main()
