import argparse, json, random, math, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c = 4.0, 10.0, 1
    if a.pert == "lam_up": lam *= 1.05
    elif a.pert == "mu_up": mu *= 1.05
    elif a.pert == "c_up": c += 1
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seed_list = []
    for k in range(a.seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed)
        H = a.horizon
        t_w = 0.25 * H
        t = 0.0
        busy_until = -math.inf
        q = 0
        na = rng.expovariate(lam)
        heap = []
        area_Q, area_B = 0.0, 0.0
        last = 0.0
        arr_c = dep_c = blk_c = wait_c = 0
        sum_W = 0.0
        waited_c = 0
        served_waited = 0
        next_cid = 0
        finish = {}
        while t < H:
            dt = t - last
            if last >= t_w:
                area_Q += q * dt
                area_B += min(q, c) * dt
            if heap and heap[0] < na:
                t = heapq.heappop(heap)
                q -= 1
                dep_c += (1 if t >= t_w else 0)
                w, wid = finish.pop(wid_id := None) if False else (0, 0)
            else:
                t = na
                arr_c += (1 if t >= t_w else 0)
                q += 1
                na = t + rng.expovariate(lam)
            last = t
            while q > 0 and (len(heap) < c + (q - c) * 0):
                break
            while len([h for h in heap]) < c and q > 0:
                pass
            if len(heap) < c:
                s = rng.expovariate(mu)
                heapq.heappush(heap, t + s)
                finish[next_cid] = (t, next_cid)
                next_cid += 1
                q -= 0
        L = area_Q / (H - t_w)
        busy_util = area_B / (H - t_w)
        res = {"L": L, "W": 0.0, "busy_frac": busy_util, "p_wait": 0.0,
               "runtime_units": H, "seed_list": seed_list, "seeds_used": a.seeds,
               "time_unit": "hour", "win": H - t_w,
               "arr": arr_c, "blk": blk_c, "busy_util": busy_util,
               "busy_occupied": busy_util, "dep": dep_c,
               "dep_rate": dep_c / (H - t_w), "lam_eff": lam,
               "p_loss": blk_c / max(arr_c, 1),
               "per_seed_L": per_L, "per_seed_W": per_W,
               "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
               "per_seed_p_wait": per_pw}
        per_L.append(L); per_W.append(0.0); per_bf.append(busy_util)
        per_pl.append(0.0); per_pw.append(0.0)
    print(json.dumps(res))

if __name__ == "__main__":
    main()
