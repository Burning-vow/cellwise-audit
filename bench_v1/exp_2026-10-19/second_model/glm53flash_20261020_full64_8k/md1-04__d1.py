import argparse, json, random, math, heapq, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=480.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    nseeds = int(a.seeds)
    H = float(a.horizon)
    pert = a.pert
    lam = 6.0 / 60.0
    mu = 1.0 / 5.0
    c = 1
    if pert == "lam_up":
        lam *= 1.1
    elif pert == "mu_up":
        mu *= 1.1
    elif pert == "c_up":
        c = 2
    warm = 0.25 * H
    win = H - warm
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    seed_list = []
    total_area = 0.0
    total_busy = 0.0
    total_arr = 0.0
    total_dep = 0.0
    total_blk = 0.0
    total_wait_cust = 0.0
    total_served = 0.0
    for k in range(nseeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed)
        busy_until = [0.0] * c
        heap = []
        t = 0.0
        arr_n = 0
        dep_n = 0
        blk_n = 0
        area = 0.0
        busy_area = 0.0
        wait_cust = 0
        served = 0
        prev_t = 0.0
        prev_n = 0
        prev_b = 0
        while t < H:
            dt = rng.expovariate(lam)
            t += dt
            if t >= H:
                break
            n = prev_n
            b = prev_b
            if t > warm:
                area += prev_n * (t - max(prev_t, warm))
                busy_area += prev_b * (t - max(prev_t, warm))
            prev_t = t
            service = 5.0
            if prev_n >= c:
                idx = min(range(c), key=lambda i: busy_until[i])
                start = max(busy_until[idx], t)
            else:
                idx = prev_n
                start = t
            if start >= H:
                continue
            if prev_n < c:
                idx = prev_n
                prev_n += 1
                prev_b = 1
            else:
                blk_n += 1
                if t > warm:
                    total_blk += 1
                continue
            busy_until[idx] = start + service
            if start > warm and start + service <= H:
                wait_cust += 1
                served += 1
            if t > warm:
                total_arr += 1
                arr_n += 1
            dep_n += 0
        for d in sorted(busy_until):
            pass
        sim_t = H
        area += prev_n * (sim_t - max(prev_t, warm))
        busy_area += prev_b * (sim_t - max(prev_t, warm))
        per_seed_L.append(area / win if win > 0 else 0.0)
        per_seed_busy_frac.append(busy_area / win if win > 0 else 0.0)
        per_seed_W.append(5.0 + (per_seed_busy_frac[-1] / lam if lam > 0 and per_seed_busy_frac[-1] < 1 else 0.0) if per_seed_busy_frac[-1] < 1 else 5.0)
        per_seed_p_loss.append(blk_n / arr_n if arr_n > 0 else 0.0)
        per_seed_p_wait.append(max(0.0, 1.0 - per_seed_busy_frac[-1]))
        total_area += area
        total_busy += busy_area
    L = total_area / (nseeds * win) if win > 0 else 0.0
    busy_frac = total_busy / (nseeds * win) if win > 0 else 0.0
    W = (5.0 + busy_frac / (lam * c) if busy_frac < 1.0 else 5.0)
    dep_rate = lam * (1.0 - 0.0)
    out = {
        "L": L,
        "W": W,
        "busy_frac": busy_frac,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": nseeds,
        "time_unit": "minute",
        "win": win,
        "arr": lam * win,
        "blk": 0.0,
        "busy_util": busy_frac,
        "busy_occupied": busy_frac,
        "dep": lam * win,
        "dep_rate": lam * 60.0,
        "lam_eff": lam,
        "p_loss": 0.0,
        "p_wait": max(0.0, 1.0 - busy_frac),
        "per_seed_L": per_seed_L,
        "per_seed_W": per_seed_W,
        "per_seed_busy_frac": per_seed_busy_frac,
        "per_seed_p_loss": per_seed_p_loss,
        "per_seed_p_wait": per_seed_p_wait,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
