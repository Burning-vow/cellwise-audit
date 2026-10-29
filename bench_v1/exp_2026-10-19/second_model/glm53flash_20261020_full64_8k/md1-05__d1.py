import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds)
    H = float(a.horizon)
    lam, mu_fixed, c = 8.0, 10.0, 1
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu_fixed *= 1.1
    elif a.pert == "c_up":
        c += 1
    time_unit = "hour"
    warm = 0.25 * H
    win = H - warm
    per_seed_L, per_seed_W, per_seed_busy = [], [], []
    per_seed_p_loss, per_seed_p_wait = [], []
    seed_list, arrs, deps, blks = [], [], [], []
    for k in range(n_seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed * 7919 + 13)
        t = 0.0
        next_arr = rng.expovariate(lam)
        busy_until = 0.0
        queue = []
        in_service = None
        area_N = 0.0
        area_busy = 0.0
        arr_n = dep_n = blk_n = 0
        wait_sum = 0.0
        waited_n = 0
        served_stay = 0.0
        served_n = 0
        while t < H:
            if next_arr <= busy_until and (not queue or next_arr <= queue[0][0] if in_service else True):
                pass
            cand = next_arr
            if in_service is not None:
                cand = min(cand, busy_until)
            if queue:
                cand = min(cand, queue[0][0])
            if cand >= H:
                area_N += (H - t) * (len(queue) + (1 if in_service else 0))
                area_busy += (H - t) * (1 if in_service else 0)
                break
            if not in_service and not queue:
                cand = min(cand, next_arr)
            if cand > t:
                n_now = len(queue) + (1 if in_service else 0)
                if t >= warm:
                    area_N += (cand - t) * n_now
                    area_busy += (cand - t) * (1 if in_service else 0)
                t = cand
            if in_service and abs(t - busy_until) < 1e-12 and (not queue or busy_until <= next_arr):
                dep_n += 1
                served_n += 1
                served_stay += t - in_service[1]
                in_service = None
            if queue and (in_service is None):
                et, st, at = queue.pop(0)
                in_service = (st, at)
                busy_until = t + st
                wait_sum += t - at
                waited_n += 1
                if t >= warm:
                    served_stay += t - at
            if next_arr <= t + 1e-12 and next_arr < H:
                arr_n += 1
                st = mu_fixed
                if in_service is None:
                    in_service = (st, t)
                    busy_until = t + st
                else:
                    queue.append((t + 1e-12, st, t))
                next_arr = t + rng.expovariate(lam) if next_arr > t + 1e-12 else t + rng.expovariate(lam)
                if next_arr <= t:
                    next_arr = t + rng.expovariate(lam)
            elif in_service and busy_until <= t + 1e-12:
                pass
        L = area_N / win
        busy_frac = area_busy / win
        pw = waited_n / arr_n if arr_n else 0.0
        per_seed_L.append(L)
        per_seed_W.append((served_stay / served_n * 60.0) if served_n else 0.0)
        per_seed_busy.append(busy_frac)
        per_seed_p_loss.append(0.0)
        per_seed_p_wait.append(pw)
        arrs.append(arr_n / win)
        deps.append(dep_n / win)
        blks.append(0.0)
    L = sum(per_seed_L) / n_seeds
    W = sum(per_seed_W) / n_seeds
    bf = sum(per_seed_busy) / n_seeds
    pwait = sum(per_seed_p_wait) / n_seeds
    arr_m = sum(arrs) / n_seeds
    dep_m = sum(deps) / n_seeds
    out = {
        "L": L, "W": W, "busy_frac": bf, "runtime_units": H,
        "seed_list": seed_list, "seeds_used": n_seeds, "time_unit": time_unit,
        "win": win, "arr": arr_m, "blk": sum(blks) / n_seeds, "dep": dep_m,
        "dep_rate": dep_m, "lam_eff": arr_m, "p_loss": 0.0, "p_wait": pwait,
        "busy_util": bf, "busy_occupied": bf,
        "per_seed_L": per_seed_L, "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy, "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
