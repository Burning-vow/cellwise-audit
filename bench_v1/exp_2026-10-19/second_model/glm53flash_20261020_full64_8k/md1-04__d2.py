import argparse, json, random, math, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam = 0.1
    svc = 5.0
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        svc /= 1.1
    elif a.pert == "c_up":
        pass

    per_L, per_W, per_busy, per_ploss, per_pwait = [], [], [], [], []
    seed_list = []
    seeds_used = 0
    tot_arr = tot_dep = tot_blk = 0.0

    for s in range(a.seeds):
        seed = a.seed_start + s
        rng = random.Random(seed)
        seed_list.append(seed)
        warm = 0.25 * a.horizon
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        busy_until = 0.0
        area_N = 0.0
        busy_time = 0.0
        arr = dep = blk = waitsum = waited_n = n_waited = 0
        last_t = 0.0
        cur_N = 0
        while t <= a.horizon:
            t2 = next_arr if not queue or (busy_until > next_arr and next_arr < busy_until) else None
            cand = []
            if next_arr <= a.horizon:
                cand.append(next_arr)
            if queue:
                cand.append(busy_until)
            if busy_until > t and busy_until <= a.horizon and not (cand and abs(cand[0]-busy_until) < 1e-12):
                cand.append(busy_until)
            if not cand:
                break
            te = min(cand)
            if te > a.horizon:
                te = a.horizon
            if te > last_t:
                dt = te - last_t
                if te > warm:
                    w0 = max(warm, last_t)
                    area_N += cur_N * (te - w0)
                    if cur_N > 0:
                        busy_time += te - w0
                last_t = te
            if abs(te - next_arr) < 1e-12:
                t = te
                arr += 1
                cur_N += 1
                if not queue and busy_until <= t:
                    start = t
                    queue.append((start, svc))
                    busy_until = start + svc
                else:
                    queue.append((t, svc))
                    busy_until = max(busy_until, t) + 0.0
                    if len(queue) == 1:
                        busy_until = t + svc
                next_arr = t + rng.expovariate(lam)
                next_arr += 0.0
                if queue and busy_until < t + 1e-12:
                    busy_until = t + svc
            elif abs(te - busy_until) < 1e-12:
                t = te
                cur_N -= 1
                dep += 1
                if queue:
                    st, dur = queue.pop(0)
                    wait = t - st - dur + dur
                    wait = t - st
                    if te > warm:
                        waitsum += wait
                        n_waited += 1
                        if wait > 1e-9:
                            waited_n += 1
                if queue:
                    st2, dur2 = queue[0]
                    if busy_until < t + 1e-12:
                        pass
                    busy_until = t + dur2
            else:
                t = te
        if queue and last_t < a.horizon:
            dt = a.horizon - last_t
            if a.horizon > warm:
                w0 = max(warm, last_t)
                area_N += cur_N * (a.horizon - w0)
                if cur_N > 0:
                    busy_time += a.horizon - w0
        win = a.horizon - warm
        L = area_N / win
        W = waitsum / n_waited if n_waited else 0.0
        bf = busy_time / win
        pw = waited_n / n_waited if n_waited else 0.0
        per_L.append(L); per_W.append(W); per_busy.append(bf)
        per_ploss.append(0.0); per_pwait.append(pw)
        tot_arr += arr; tot_dep += dep; tot_blk += blk
        seeds_used += 1

    Ws = sum(per_W) / seeds_used
    Ls = sum(per_L) / seeds_used
    bs = sum(per_busy) / seeds_used
    out = {
        "L": Ls, "W": Ws, "busy_frac": bs,
        "busy_util": bs, "busy_occupied": bs,
        "runtime_units": a.horizon, "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": "minute",
        "win": a.horizon * 0.75,
        "arr": tot_arr / seeds_used, "dep": tot_dep / seeds_used,
        "blk": tot_blk / seeds_used,
        "dep_rate": tot_dep / seeds_used / (a.horizon * 0.75) * 60.0,
        "lam_eff": lam * 60.0, "p_loss": 0.0,
        "p_wait": sum(per_pwait) / seeds_used,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy,
        "per_seed_p_loss": per_ploss, "per_seed_p_wait": per_pwait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
