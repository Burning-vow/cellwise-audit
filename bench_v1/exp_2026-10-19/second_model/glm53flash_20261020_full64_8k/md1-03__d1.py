import argparse, json, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam_hr = 6.0
    service_base = 6.0
    c = 1
    if a.pert == "lam_up":
        lam_hr *= 1.1
    elif a.pert == "mu_up":
        service_base /= 1.1
    elif a.pert == "c_up":
        c = 2

    time_unit = "minute"
    lam = lam_hr / 60.0
    horizon = a.horizon
    warm = 0.25 * horizon
    win = horizon - warm

    per_L, per_W, per_busy, per_ploss, per_pwait = [], [], [], [], []
    seed_list = []
    g_arr = g_dep = g_blk = 0.0
    g_busy_area = g_n_area = 0.0
    g_waitn = g_arrn = 0.0

    for si in range(a.seeds):
        seed = a.seed_start + si
        rng = random.Random(seed)
        t = 0.0
        N = 0
        queue = []
        in_svc = []
        next_arr = rng.expovariate(lam)
        area_n = area_busy = 0.0
        n_arr = n_dep = n_blk = n_wait = 0
        w_sum = 0.0
        w_arrn = 0.0
        w_dep = 0

        def integrate(t0, t1, N):
            dt = max(0.0, t1 - t0)
            lo = max(t0, warm)
            hi = max(lo, min(t1, horizon))
            eff = hi - lo
            return dt, eff * N, eff * min(N, 1)

        while t < horizon:
            next_dep = min(in_svc) if in_svc else math.inf
            if next_arr <= next_dep and next_arr < horizon:
                dt, an, ab = integrate(t, next_arr, N)
                area_n += an; area_busy += ab
                t = next_arr
                N += 1
                svc = service_base
                if t >= warm:
                    n_arr += 1
                    w_arrn += 1.0
                if len(in_svc) < c:
                    in_svc.append(t + svc)
                    if t >= warm:
                        pass
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        n_wait += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if next_dep > horizon:
                    dt, an, ab = integrate(t, horizon, N)
                    area_n += an; area_busy += ab
                    t = horizon
                    break
                dt, an, ab = integrate(t, next_dep, N)
                area_n += an; area_busy += ab
                t = next_dep
                in_svc.remove(t)
                N -= 1
                if queue:
                    at, svc = queue.pop(0)
                    in_svc.append(t + svc)
                    if t >= warm:
                        w_sum += t - at
                        w_dep += 1
                else:
                    if t >= warm:
                        w_dep += 1
                if t >= warm:
                    n_dep += 1

        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        Wv = (w_sum / w_dep) if w_dep > 0 else 0.0
        pl = 0.0
        pw = (n_wait / n_arr) if n_arr > 0 else 0.0
        per_L.append(L); per_W.append(Wv); per_busy.append(bf)
        per_ploss.append(pl); per_pwait.append(pw)
        seed_list.append(seed)
        g_arr += n_arr / win; g_dep += n_dep / win; g_blk += n_blk / win
        g_busy_area += bf; g_n_area += L
        g_waitn += pw; g_arrn += 1

    nS = a.seeds
    Lm = sum(per_L) / nS
    Wm = sum(per_W) / nS
    bfm = sum(per_busy) / nS
    dep_rate = (g_dep / nS) * 60.0
    out = {
        "L": Lm, "W": Wm, "busy_frac": bfm,
        "busy_util": Lm / c, "busy_occupied": bfm,
        "runtime_units": time_unit, "time_unit": time_unit,
        "seed_list": seed_list, "seeds_used": nS,
        "win": win,
        "arr": g_arr / nS, "dep": g_dep / nS, "blk": g_blk / nS,
        "dep_rate": dep_rate,
        "lam_eff": (g_arr / nS) / win * 60.0,
        "p_loss": 0.0, "p_wait": g_waitn / nS,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy,
        "per_seed_p_loss": per_ploss, "per_seed_p_wait": per_pwait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
