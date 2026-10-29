import argparse, json, math, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu1, mu2 = 6.0, 10.0, 10.0
    if a.pert == "lam_up": lam = 7.2
    elif a.pert == "mu_up": mu1 = mu2 = 12.0
    elif a.pert == "c_up": mu1 = mu2 = 8.0
    H = a.horizon
    warm = 0.25 * H
    win = H - warm
    per_L, per_W, per_busy, per_ploss, per_pwait = [], [], [], [], []
    seed_list = []
    sum_arr = sum_dep = sum_blk = sum_busyfrac = 0.0
    for k in range(a.seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed * 2654435761 % (2**31) + 12345)
        t = 0.0
        n1 = n2 = 0
        next_arr = rng.expovariate(lam)
        dep1 = dep2 = math.inf
        area = 0.0
        busy1 = busy2 = 0.0
        last = 0.0
        sojourns = []
        arrivals_w = 0
        waited_w = 0
        area_done = False
        while t < H:
            t_next = min(next_arr, dep1, dep2)
            if t_next >= H: t_next = H
            # integrate before state change
            a_lo = max(last, warm)
            if t_next > warm:
                seg = t_next - a_lo if a_lo < t_next else 0.0
                if seg > 0:
                    area += (n1 + n2) * seg
                    busy1 += (1 if n1 > 0 else 0) * seg
                    busy2 += (1 if n2 > 0 else 0) * seg
            t = t_next
            if t >= H: break
            if next_arr == t:
                arrivals_in = True
                if t >= warm:
                    arrivals_w += 1
                    if n1 > 0: waited_w += 1
                s1 = rng.expovariate(mu1)
                s2 = rng.expovariate(mu2)
                n1 += 1
                if n1 == 1:
                    dep1 = t + s1
                next_arr = t + rng.expovariate(lam)
            elif dep1 == t:
                n1 -= 1
                if n2 > 0 and t >= warm: waited_w += 1
                n2 += 1
                if n1 > 0:
                    dep1 = t + rng.expovariate(mu1)
                else:
                    dep1 = math.inf
                if n2 == 1:
                    dep2 = t + rng.expovariate(mu2)
            else:
                n2 -= 1
                if n2 > 0:
                    dep2 = t + rng.expovariate(mu2)
                else:
                    dep2 = math.inf
            last = t
        L = area / win
        per_L.append(L)
        per_busy.append((busy1 + busy2) / (2.0 * win))
        per_W.append(0.0 if len(sojourns) == 0 else sum(sojourns) / len(sojourns))
        per_ploss.append(0.0)
        per_pwait.append(waited_w / arrivals_w if arrivals_w > 0 else 0.0)
        sum_arr += arrivals_w
        sum_dep += arrivals_w
        sum_blk += 0.0
        sum_busyfrac += (busy1 + busy2) / (2.0 * win)
    n = a.seeds
    out = {
        "L": sum(per_L) / n,
        "W": sum(per_W) / n,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "win": win,
        "arr": sum_arr / n,
        "blk": sum_blk / n,
        "busy_frac": sum_busyfrac / n,
        "busy_util": sum_busyfrac / n,
        "dep": sum_dep / n,
        "dep_rate": sum_dep / n / win,
        "lam_eff": sum_dep / n / win,
        "p_loss": sum(per_ploss) / n,
        "p_wait": sum(per_pwait) / n,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_busy,
        "per_seed_p_loss": per_ploss,
        "per_seed_p_wait": per_pwait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
