import argparse, json, random, math

def run_seed(seed, H, lam, mu, C, warm):
    rng = random.Random(seed)
    t = 0.0; n = 0
    area = 0.0; busy_area = 0.0
    arr = dep = blk = 0
    waits = []
    nxt_arr = rng.expovariate(lam)
    dep_t = math.inf
    while True:
        t_next = min(nxt_arr, dep_t)
        if t_next > H: t_next = H
        if t >= warm and t_next > t:
            area += n * (t_next - t)
            if n > 0: busy_area += (t_next - t)
        t = t_next
        if t >= H: break
        if nxt_arr <= dep_t:
            if n < C:
                waits.append(t if t >= warm else None)
                svc = rng.expovariate(mu)
                n += 1
                if t >= warm: arr += 1
                if n == 1: dep_t = t + svc
            else:
                if t >= warm: blk += 1
            nxt_arr = t + rng.expovariate(lam)
        else:
            n -= 1
            if t >= warm: dep += 1
            if n == 0: dep_t = math.inf
            else: dep_t = t + rng.expovariate(mu)
    return area, busy_area, arr, dep, blk, [w for w in waits if w is not None]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, C = 8.0, 10.0, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": C += 1
    H = a.horizon; warm = 0.25 * H
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    per_L=[]; per_W=[]; per_bf=[]; per_pl=[]; per_pw=[]
    tarr=tdep=tblk=0
    for s in seeds:
        area, barea, arr, dep, blk, waits = run_seed(s, H, lam, mu, C, warm)
        win = H - warm
        L = area / win
        w = sum(waits)/len(waits) if waits else 0.0
        p_wait = len(waits)/arr if arr else 0.0
        per_L.append(L); per_W.append(w); per_bf.append(barea/win)
        per_pl.append(blk/arr if arr else 0.0); per_pw.append(p_wait)
        tarr+=arr; tdep+=dep; tblk+=blk
    k = len(seeds)
    out = {
        "L": sum(per_L)/k, "W": sum(per_W)/k, "busy_frac": sum(per_bf)/k,
        "p_loss": sum(per_pl)/k, "runtime_units": H, "seed_list": seeds,
        "seeds_used": k, "time_unit": "hour", "win": H - warm,
        "arr": tarr/k, "blk": tblk/k, "busy_util": sum(per_bf)/k,
        "busy_occupied": sum(per_bf)/k, "dep": tdep/k,
        "dep_rate": (tdep/k)/ (H - warm), "lam_eff": (tarr/k)/(H - warm),
        "p_wait": sum(per_pw)/k,
        "per_seed_L": per_L, "per_seed_W": per_W, "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
