import argparse, json, random, math, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=20000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); horizon = float(a.horizon); s0 = int(a.seed_start)
    lam, mu, c = 8.0, 10.0, 1
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    warm = 0.25
    t_warm = warm * horizon
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    for k in range(n_seeds):
        seed = s0 + k
        rng = random.Random(seed)
        seed_list.append(seed)
        t = 0.0; n = 0
        area = 0.0; busy = 0.0
        wsum = 0.0; ncomp = 0
        waits = 0.0; nwait = 0
        arr_w = dep_w = blk_w = 0
        busy_last = 0.0
        while True:
            ta = t + rng.expovariate(lam)
            ts = t + rng.expovariate(mu) if n > 0 else math.inf
            t_next = min(ta, ts, horizon)
            if t_next >= horizon:
                t_next = horizon
            if t_next > t_warm:
                a0 = max(t, t_warm)
                area += n * (t_next - a0)
                busy += busy_last * (t_next - a0)
            if t_next == horizon:
                break
            if ta <= ts:
                t = ta
                if n < c + (0):
                    svc = rng.expovariate(mu)
                    if t >= t_warm:
                        arr_w += 1
                    if n < c:
                        n += 1
                        heapq.heappush(busy_q := [], t + svc) if False else None
                        if n == 1:
                            busy_last = 1.0
                            dep_t = t + svc
                            ts = dep_t
                        else:
                            dep_t = ts + svc
                            ts = dep_t
                        arrivals.append((t, svc, dep_t)) if False else None
                        pending.append((t, svc, dep_t))
                    else:
                        pending.append((t, svc, None))
                        blk_w += 1 if t >= t_warm else 0
                        n += 1
                else:
                    pass
            else:
                t = ts
                dep_t = t
                while pending and pending[0][2] is not None and pending[0][2] <= t + 1e-12:
                    at, sv, dt = pending.pop(0)
                    if n > 0: n -= 1
                    if t >= t_warm:
                        wsum += (dt - at); ncomp += 1
                        dep_w += 1
                    if n > 0:
                        busy_last = 1.0
                        next_item = None
                        for i, p in enumerate(pending):
                            if p[2] is None:
                                next_item = i; break
                        if next_item is not None:
                            at2, sv2, _ = pending.pop(next_item)
                            pending.append((at2, sv2, t + sv2))
                            ts = t + sv2
                            if t >= t_warm: nwait += 1
                    else:
                        busy_last = 0.0
                        ts = math.inf
                continue_flag = True
            break_out = False
            if break_out: break
        per_L.append(area / (horizon - t_warm))
        per_bf.append(busy / (horizon - t_warm))
        per_W.append(wsum / ncomp if ncomp else 0.0)
        per_pl.append(blk_w / arr_w if arr_w else 0.0)
        per_pw.append(nwait / ncomp if ncomp else 0.0)
        tot_arr += arr_w; tot_dep += dep_w; tot_blk += blk_w
    win = horizon - t_warm
    out = {
        "L": sum(per_L) / n_seeds, "W": sum(per_W) / n_seeds,
        "busy_frac": sum(per_bf) / n_seeds,
        "p_wait": sum(per_pw) / n_seeds,
        "runtime_units": horizon, "seed_list": seed_list, "seeds_used": n_seeds,
        "time_unit": "hour", "win": win,
        "arr": tot_arr / n_seeds, "blk": tot_blk / n_seeds,
        "busy_util": sum(per_bf) / n_seeds, "dep": tot_dep / n_seeds,
        "dep_rate": tot_dep / n_seeds / win,
        "lam_eff": tot_arr / n_seeds / win,
        "p_loss": sum(per_pl) / n_seeds,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
