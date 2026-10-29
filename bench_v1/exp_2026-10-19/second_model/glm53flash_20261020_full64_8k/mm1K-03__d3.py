import json, random, argparse, math

def run_seed(seed, H, lam, mu, c, K, warm):
    rng = random.Random(seed)
    t = 0.0; n = 0
    q = []
    dep_time = math.inf
    arr_t = 0.0
    stats = {"area": 0.0, "busy": 0.0, "arr": 0, "dep": 0, "blk": 0, "waited": 0, "admitted": 0, "wsum": 0.0}
    dep_records = []
    arrival_queue = []
    while True:
        next_arr = arr_t if arr_t < H else math.inf
        t_next = min(next_arr, dep_time)
        if t_next == math.inf or t_next >= H:
            if warm < H:
                stats["area"] += n * (H - max(t, warm))
                if n > 0:
                    stats["busy"] += (H - max(t, warm))
            break
        if warm > t:
            dt_int = max(0.0, min(t_next, H) - max(t, warm))
            stats["area"] += n * dt_int
            if n > 0:
                stats["busy"] += dt_int
        t = t_next
        if t == next_arr:
            at = t
            s = rng.expovariate(mu)
            arr_t = t + rng.expovariate(lam)
            if arr_t >= H:
                arr_t = math.inf
            if t >= warm:
                stats["arr"] += 1
            if n < K:
                if t >= warm:
                    stats["admitted"] += 1
                    if n > 0:
                        stats["waited"] += 1
                n += 1
                arrival_queue.append([at, s])
                if n == 1:
                    dep_time = t + s
            else:
                if t >= warm:
                    stats["blk"] += 1
        else:
            st, sv = arrival_queue.pop(0)
            if t >= warm:
                stats["dep"] += 1
                stats["wsum"] += t - st
                dep_records.append(1)
            n -= 1
            if n > 0:
                dep_time = t + arrival_queue[0][1]
            else:
                dep_time = math.inf
    win = H - warm
    L = stats["area"] / win
    busy_frac = stats["busy"] / win
    W = stats["wsum"] / stats["dep"] if stats["dep"] else 0.0
    p_loss = stats["blk"] / stats["arr"] if stats["arr"] else 0.0
    p_wait = stats["waited"] / stats["admitted"] if stats["admitted"] else 0.0
    return {"L": L, "W": W, "busy_frac": busy_frac, "p_loss": p_loss,
            "p_wait": p_wait, "arr": stats["arr"], "dep": stats["dep"], "blk": stats["blk"]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=1000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    lam, mu, c, K = 8.0, 10.0, 1, 4
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    H = a.horizon
    warm = 0.25 * H
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    res = [run_seed(s, H, lam, mu, c, K, warm) for s in seed_list]
    m = len(res)
    out = {
        "L": sum(r["L"] for r in res) / m,
        "W": sum(r["W"] for r in res) / m,
        "busy_frac": sum(r["busy_frac"] for r in res) / m,
        "busy_occupied": sum(r["busy_frac"] for r in res) / m,
        "busy_util": sum(r["busy_frac"] for r in res) / m / c,
        "p_loss": sum(r["p_loss"] for r in res) / m,
        "p_wait": sum(r["p_wait"] for r in res) / m,
        "lam_eff": sum(r["dep"] for r in res) / m / (H - warm),
        "dep_rate": sum(r["dep"] for r in res) / m / (H - warm),
        "arr": sum(r["arr"] for r in res) / m,
        "dep": sum(r["dep"] for r in res) / m,
        "blk": sum(r["blk"] for r in res) / m,
        "runtime_units": H,
        "win": H - warm,
        "time_unit": "hour",
        "seed_list": seed_list,
        "seeds_used": m,
        "per_seed_L": [r["L"] for r in res],
        "per_seed_W": [r["W"] for r in res],
        "per_seed_busy_frac": [r["busy_frac"] for r in res],
        "per_seed_p_loss": [r["p_loss"] for r in res],
        "per_seed_p_wait": [r["p_wait"] for r in res],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
