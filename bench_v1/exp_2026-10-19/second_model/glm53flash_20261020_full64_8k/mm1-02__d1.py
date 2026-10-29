import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=0)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam, mu = 4.0, 12.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": lam *= 1.0

    warm = 0.25 * a.horizon
    win = a.horizon - warm

    per_L, per_W, per_busy, per_pwait, per_ploss = [], [], [], [], []
    sum_arr = sum_dep = sum_blk = 0.0
    seed_list = []

    for k in range(a.seeds):
        seed = a.seed_start + k
        rng = random.Random(seed)
        seed_list.append(seed)

        t = 0.0
        t_arr = rng.expovariate(lam)
        busy_until = None
        queue = []
        n = 0
        area_L = 0.0
        area_busy = 0.0
        last_t = 0.0
        waits = []
        sojourns = []
        arr_c = dep_c = blk_c = 0
        last_change = 0.0

        def integrate(now):
            nonlocal area_L, area_busy, last_t
            dt = now - last_t
            area_L += n * dt
            if n >= 1:
                area_busy += dt
            last_t = now

        while t_arr < a.horizon:
            nxt_dep = busy_until if busy_until is not None else math.inf
            t = min(t_arr, nxt_dep)
            if t >= a.horizon:
                break
            integrate(t)
            if t_arr <= nxt_dep:
                t = t_arr
                arr_c += 1
                svc = rng.expovariate(mu)
                if n == 0 and busy_until is None:
                    busy_until = t + svc
                    waits.append(0.0)
                    heapq.heappush(queue, (busy_until, svc))
                else:
                    heapq.heappush(queue, (t + svc, svc))
                if n >= 1:
                    waits.append(busy_until - t if False else 0.0)
                n += 1
                t_arr += rng.expovariate(lam)
            else:
                t = nxt_dep
                heapq.heappop(queue)
                n -= 1
                dep_c += 1
                if n > 0:
                    nd, sv = queue[0]
                    busy_until = nd
                else:
                    busy_until = None
            last_change = t

        integrate(a.horizon)

        wL = area_L / a.horizon
        wbusy = area_busy / a.horizon
        pwait = 1.0 if wbusy >= 1.0 else min(1.0, max(0.0, wbusy))
        per_L.append(wL)
        per_W.append(0.0 if not waits else sum(waits) / len(waits))
        per_busy.append(wbusy)
        per_pwait.append(pwait)
        per_ploss.append(0.0)
        sum_arr += arr_c / win if win > 0 else 0
        sum_dep += dep_c / win if win > 0 else 0
        sum_blk += 0.0

    seeds_used = a.seeds
    L = sum(per_L) / seeds_used
    pwait = sum(per_pwait) / seeds_used
    rho = lam / mu
    W = L / lam * 60.0 if lam > 0 else 0.0

    out = {
        "L": L,
        "W": W,
        "busy_frac": L,
        "p_wait": pwait,
        "runtime_units": a.horizon,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": win,
        "arr": sum_arr,
        "blk": sum_blk,
        "busy_util": L,
        "busy_occupied": L,
        "dep": sum_dep,
        "dep_rate": sum_dep / win if win > 0 else 0.0,
        "lam_eff": lam,
        "p_loss": 0.0,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy,
        "per_seed_p_loss": per_ploss,
        "per_seed_p_wait": per_pwait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
