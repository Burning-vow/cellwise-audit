import sys, json, argparse, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", dest="seed_start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); s0 = int(a.seed_start)
    lam = 7.0 / 60.0; mu = 1.0 / 6.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": mu *= 1.5
    warm = H * 0.25; win = H - warm
    seed_list = []; per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    arr_tot = dep_tot = blk_tot = bw_tot = nwait_tot = 0.0
    area_tot = busyarea_tot = 0.0
    for k in range(n_seeds):
        seed = s0 + k; seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0; queue = []; busy_until = None
        next_arr = rng.expovariate(lam)
        area = 0.0; busyarea = 0.0
        arr = dep = blk = nw = 0; waits = []
        last = 0.0
        def record(t0, t1, n, busy):
            nonlocal area, busyarea
            area += n * (t1 - t0)
            busyarea += min(n, 1) * (t1 - t0)
        while t < H:
            t0 = t
            if busy_until is None or next_arr < busy_until:
                t = next_arr
                record(t0, t, len(queue) + (1 if busy_until is not None else 0), True)
                arr += 1
                svc = rng.expovariate(mu)
                if busy_until is None:
                    busy_until = t + svc
                else:
                    queue.append((t, svc))
                    nw += 1
                next_arr = t + rng.expovariate(lam)
            else:
                t = busy_until
                record(t0, t, 1 + len(queue), True)
                dep += 1
                if queue:
                    a_t, svc = queue.pop(0)
                    waits.append(t - a_t)
                    busy_until = t + svc
                else:
                    busy_until = None
        if busy_until is None:
            record(t0, t, len(queue), False)
        if t < H:
            t1 = H
            record(t0, t1, len(queue) + (1 if busy_until is not None else 0), True)
            t = t1
        area = area * (win / max(win, 1e-12))
        def rec2(t0, t1, n):
            nonlocal area, busyarea
            area += n * (t1 - t0)
            busyarea += min(n, 1) * (t1 - t0)
        per_L.append(area / win)
        per_W.append((sum(waits) + sum(1 for _ in queue) * 0) / max(len(waits), 1))
        per_bf.append(busyarea / win)
        per_pl.append(0.0)
        per_pw.append(nw / max(arr, 1))
        arr_tot += arr; dep_tot += dep; blk_tot += blk
        nwait_tot += nw
        area_tot += area; busyarea_tot += busyarea
        waits_all = waits
        per_W[-1] = sum(waits_all) / max(len(waits_all), 1)
    n = max(n_seeds, 1)
    W_all = sum(per_W) / n
    out = {
        "L": area_tot / n / win,
        "W": W_all,
        "busy_frac": busyarea_tot / n / win,
        "p_wait": nwait_tot / max(arr_tot, 1),
        "runtime_units": float(H),
        "seed_list": seed_list,
        "seeds_used": n_seeds,
        "time_unit": "minute",
        "win": win,
        "arr": arr_tot / n,
        "dep": dep_tot / n,
        "blk": blk_tot / n,
        "dep_rate": dep_tot / n / win * 60.0,
        "lam_eff": lam * 60.0,
        "p_loss": blk_tot / max(arr_tot, 1),
        "busy_util": busyarea_tot / n / win,
        "busy_occupied": busyarea_tot / n / win,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
