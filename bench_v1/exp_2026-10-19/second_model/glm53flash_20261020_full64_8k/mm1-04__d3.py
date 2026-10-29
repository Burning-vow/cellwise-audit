import argparse, json, heapq, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=200.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu_s = 6.0, 12.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu_s *= 1.1
    elif a.pert == "c_up": mu_s *= 1/1.1
    H = a.horizon
    warm = 0.25 * H
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seeds_used, seed_list = 0, []
    tot_arr = tot_dep = tot_blk = 0.0
    for k in range(a.seeds):
        sd = a.seed_start + k
        rng = random.Random(sd)
        t = 0.0
        nxt_arr = rng.expovariate(lam)
        events = []
        heapq.heappush(events, (nxt_arr, 0))
        busy_until = -1.0
        queue = []
        area_L = 0.0
        area_busy = 0.0
        sum_wait = 0.0
        n_arr = n_dep = n_blk = 0
        n_wait = 0
        served_wait = 0
        last = 0.0
        while t < H:
            if not events: break
            t, typ = heapq.heappop(events)
            if t > H: break
            if t >= warm:
                dt = t - last
                n = len(queue) + (1 if busy_until > t else 0)
                area_L += n * dt
                area_busy += min(n, 1) * dt
            last = t
            if typ == 0:
                n_arr += 1
                if t >= warm: pass
                svc = rng.expovariate(mu_s)
                if busy_until <= t:
                    busy_until = t + svc
                    heapq.heappush(events, (t + svc, 1))
                else:
                    queue.append((t, svc))
                heapq.heappush(events, (t + rng.expovariate(lam), 0))
            else:
                n_dep += 1
                if queue:
                    at, svc = queue.pop(0)
                    if at >= warm:
                        sum_wait += (t - at); served_wait += 1
                        if t - at > 0: n_wait += 1
                    n_wait += 0
                    busy_until = t + svc
                    heapq.heappush(events, (t + svc, 1))
                else:
                    busy_until = -1.0
        tail = H - warm
        if tail <= 0: continue
        seeds_used += 1
        seed_list.append(sd)
        L = area_L / tail
        bf = area_busy / tail
        cnt_arr = sum(1 for _ in []) 
        per_L.append(L)
        per_W.append((sum_wait / served_wait) * 60.0 if served_wait else 0.0)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append((n_wait / n_arr) if n_arr else 0.0)
        tot_arr += n_arr; tot_dep += n_dep; tot_blk += 0.0
    n = max(seeds_used, 1)
    W = sum(per_W) / n
    Lm = sum(per_L) / n
    out = {
        "L": Lm, "W": W,
        "busy_frac": sum(per_bf)/n,
        "p_wait": sum(per_pw)/n,
        "runtime_units": "hour", "time_unit": "hour",
        "seed_list": seed_list, "seeds_used": seeds_used,
        "win": H * 0.75,
        "arr": tot_arr/n, "dep": tot_dep/n, "blk": tot_blk/n,
        "dep_rate": (tot_dep/n)/(H*0.75),
        "lam_eff": lam, "p_loss": 0.0,
        "busy_util": sum(per_bf)/n,
        "busy_occupied": sum(per_bf)/n,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
