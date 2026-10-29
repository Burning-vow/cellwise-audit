import argparse, json, math, random, heapq
from collections import deque

def run_one(seed, H, lam, mu, c):
    rng = random.Random(seed)
    warm = 0.25 * H
    t = 0.0
    n = 0
    q = deque()
    busy = []
    next_arr = rng.expovariate(lam)
    areaN = 0.0
    areaB = 0.0
    areaU = 0.0
    arr_cnt = 0
    dep_cnt = 0
    wait_cnt = 0
    soj_sum = 0.0
    while t < H:
        t1 = min(next_arr, (busy[0] if busy else math.inf), H)
        w0 = max(t, warm)
        if t1 > w0:
            dt = t1 - w0
            areaN += n * dt
            areaB += min(n, 1) * dt
            areaU += min(n, c) * dt
        if t1 >= H:
            break
        if next_arr <= (busy[0] if busy else math.inf):
            waited = n >= 1
            n += 1
            if t1 >= warm:
                arr_cnt += 1
                if waited:
                    wait_cnt += 1
            serv = rng.expovariate(mu)
            rec = (t1, serv, waited)
            if len(busy) < c:
                heapq.heappush(busy, t1 + serv)
            else:
                q.append(rec)
            next_arr = t1 + rng.expovariate(lam)
        else:
            heapq.heappop(busy)
            n -= 1
            if q:
                a, s, w = q.popleft()
                heapq.heappush(busy, t1 + s)
            if t1 >= warm:
                dep_cnt += 1
        t = t1
    win = H - warm
    L = areaN / win
    W = (soj_sum / dep_cnt) * 60.0 if dep_cnt else 0.0
    busy_frac = areaB / win
    p_wait = wait_cnt / arr_cnt if arr_cnt else 0.0
    return {"L": L, "W": W, "busy_frac": busy_frac, "p_wait": p_wait,
            "arr": arr_cnt, "dep": dep_cnt, "busy_util": areaU / (win * c)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=float, default=10)
    p.add_argument("--horizon", type=float, default=10000)
    p.add_argument("--seed-start", type=float, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    n_seeds = int(a.seeds)
    H = float(a.horizon)
    s0 = int(a.seed_start)
    lam, mu, c = 6.0, 10.0, 1
    if a.pert == "lam_up":
        lam *= 1.1
    elif a.pert == "mu_up":
        mu *= 1.1
    elif a.pert == "c_up":
        c = 2
    seed_list = list(range(s0, s0 + n_seeds))
    per = [run_one(s, H, lam, mu, c) for s in seed_list]
    win = H - 0.25 * H
    def avg(k):
        return sum(d[k] for d in per) / len(per)
    arr = avg("arr"); dep = avg("dep")
    out = {
        "L": avg("L"),
        "W": avg("W"),
        "busy_frac": avg("busy_frac"),
        "p_wait": avg("p_wait"),
        "busy_util": avg("busy_util"),
        "busy_occupied": avg("busy_frac"),
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": len(seed_list),
        "time_unit": "hour",
        "win": win,
        "arr": arr,
        "blk": 0.0,
        "dep": dep,
        "dep_rate": dep / win,
        "lam_eff": arr / win,
        "p_loss": 0.0,
        "per_seed_L": [d["L"] for d in per],
        "per_seed_W": [d["W"] for d in per],
        "per_seed_busy_frac": [d["busy_frac"] for d in per],
        "per_seed_p_loss": [0.0] * len(per),
        "per_seed_p_wait": [d["p_wait"] for d in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
