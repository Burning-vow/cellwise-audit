import argparse, json, math, random, heapq

def draw_service(rng, p, mu1, mu2):
    return rng.expovariate(mu1) if rng.random() < p else rng.expovariate(mu2)

def run_seed(seed, horizon, warm, lam, p, mu1, mu2):
    rng = random.Random(seed)
    t = 0.0
    queue = []
    busy_until = None
    events = []
    heapq.heapify(events)
    next_arr = rng.expovariate(lam)
    heapq.heappush(events, (next_arr, 0))
    n = 0
    area_N = 0.0
    area_B = 0.0
    arr_n = 0
    dep_n = 0
    wait_sum = 0.0
    wait_cnt = 0
    prev_t = 0.0
    done = False
    while not done:
        t_ev, kind = heapq.heappop(events)
        if t_ev > horizon:
            t_ev = horizon
            done = True
        dt = t_ev - prev_t
        if prev_t >= warm:
            area_N += n * dt
            area_B += (1 if n >= 1 else 0) * dt
        elif t_ev > warm:
            w = t_ev - warm
            area_N += n * w
            area_B += (1 if n >= 1 else 0) * w
        prev_t = t_ev
        t = t_ev
        if done:
            break
        if kind == 0:
            s = draw_service(rng, p, mu1, mu2)
            heapq.heappush(events, (t + rng.expovariate(lam), 0))
            if prev_t >= warm or t >= warm:
                pass
            if t >= warm:
                arr_n += 1
            if n == 0:
                heapq.heappush(events, (t + s, 1))
                if t >= warm:
                    pass
            else:
                queue.append((t, s))
                if t >= warm:
                    wait_cnt += 1
            n += 1
            if t >= warm and n > 1:
                pass
        else:
            dep_n += 1 if t >= warm else 0
            n -= 1
            if queue:
                at, s = queue.pop(0)
                if t >= warm:
                    wait_sum += t - at
                heapq.heappush(events, (t + s, 1))
    win = horizon - warm
    N = area_N / win if win > 0 else 0.0
    B = area_B / win if win > 0 else 0.0
    p_wait = wait_cnt / arr_n if arr_n > 0 else 0.0
    W = wait_sum / arr_n if arr_n > 0 else 0.0
    return {"L": N, "W": W * 60.0, "busy": B, "arr": arr_n, "dep": dep_n,
            "p_loss": 0.0, "p_wait": p_wait, "win": win}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=100000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam = 3.0
    mu = 10.0
    cv2 = 9.0
    p = 0.5 * (1.0 + math.sqrt((cv2 - 1.0) / (cv2 + 1.0)))
    m = 6.0 / 60.0
    mu1 = 2.0 * p / m
    mu2 = 2.0 * (1.0 - p) / m
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu1 *= 1.1
        mu2 *= 1.1
    elif a.pert == "c_up":
        pass
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    warm = 0.25 * a.horizon
    res = []
    for s in seed_list:
        res.append(run_seed(s, a.horizon, warm, lam / 60.0, p, mu1, mu2))
    k = len(res)
    L = sum(r["L"] for r in res) / k
    W = sum(r["W"] for r in res) / k
    bf = sum(r["busy"] for r in res) / k
    arr = sum(r["arr"] for r in res) / k
    dep = sum(r["dep"] for r in res) / k
    pl = sum(r["p_loss"] for r in res) / k
    pw = sum(r["p_wait"] for r in res) / k
    win = res[0]["win"]
    out = {
        "L": L, "W": W, "busy_frac": bf, "runtime_units": "min",
        "seed_list": seed_list, "seeds_used": k, "time_unit": "minute",
        "win": win, "arr": arr, "blk": 0.0, "busy_util": bf,
        "busy_occupied": bf, "dep": dep,
        "dep_rate": dep / win * 60.0, "lam_eff": arr / win * 60.0,
        "p_loss": pl, "p_wait": pw,
        "per_seed_L": [r["L"] for r in res],
        "per_seed_W": [r["W"] for r in res],
        "per_seed_busy_frac": [r["busy"] for r in res],
        "per_seed_p_loss": [r["p_loss"] for r in res],
        "per_seed_p_wait": [r["p_wait"] for r in res],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
