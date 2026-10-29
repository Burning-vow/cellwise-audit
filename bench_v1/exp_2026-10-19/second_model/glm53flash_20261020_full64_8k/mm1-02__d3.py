import json, argparse, heapq, random, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--horizon", type=float, default=400.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam, mu, c = 4.0, 12.0, 1
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    warm = 0.25 * a.horizon
    per_L, per_W, per_busy, per_pw, per_pl = [], [], [], [], []
    seeds_used = 0
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        t = 0.0
        na = 0.0
        events = []
        heapq.heappush(events, (rng.expovariate(lam), "a", 0))
        q = []
        busy_until = [None]*c
        n = 0
        area_N = 0.0
        area_B = 0.0
        area_Q = 0.0
        sW = 0.0
        wcnt = 0
        waits = []
        arr_w = dep_w = blk_w = 0
        last = 0.0
        t_end = a.horizon
        while events:
            te, kind, idx = heapq.heappop(events)
            if te > t_end: break
            dt = te - last
            area_N += n * dt
            area_B += sum(1 for b in busy_until if b is not None and b > te) * dt if False else (c - sum(1 for b in busy_until if b is None)) * dt
            area_Q += len(q) * dt
            last = te
            t = te
            if kind == "a":
                if te >= warm: arr_w += 1
                svc = rng.expovariate(mu)
                free = [j for j in range(c) if busy_until[j] is None or busy_until[j] <= te]
                if free:
                    j = free[0]
                    busy_until[j] = te + svc
                    heapq.heappush(events, (te + svc, "d", j))
                else:
                    heapq.heappush(q, (te, svc))
                heapq.heappush(events, (te + rng.expovariate(lam), "a", 0))
            else:
                busy_until[idx] = None
                if te >= warm: dep_w += 1
                if q:
                    at, svc = heapq.heappop(q)
                    waits.append(te - at)
                    busy_until[idx] = te + svc
                    heapq.heappush(events, (te + svc, "d", idx))
        seeds_used += 1
        seed_list.append(seed)
        win = a.horizon - warm
        L = area_N / win if win > 0 else 0.0
        B = area_B / win if win > 0 else 0.0
        per_L.append(L)
        per_W.append(sum(waits)/len(waits)*60 if waits else 0.0)
        per_busy.append(B / c)
        per_pw.append(len(waits)/arr_w if arr_w else 0.0)
        per_pl.append(blk_w/arr_w if arr_w else 0.0)
        tot_arr += arr_w / win if win > 0 else 0.0
        tot_dep += dep_w / win if win > 0 else 0.0
        tot_blk += blk_w / win if win > 0 else 0.0
    def avg(x): return sum(x)/len(x) if x else 0.0
    out = {
        "L": avg(per_L), "W": avg(per_W), "busy_frac": avg(per_busy),
        "p_wait": avg(per_pw), "runtime_units": a.horizon, "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": "hour", "win": a.horizon - warm,
        "arr": tot_arr/a.seeds, "blk": tot_blk/a.seeds, "busy_util": avg(per_busy),
        "busy_occupied": avg(per_busy), "dep": tot_dep/a.seeds,
        "dep_rate": tot_dep/a.seeds, "lam_eff": tot_arr/a.seeds,
        "p_loss": avg(per_pl),
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
