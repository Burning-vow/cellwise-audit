import argparse, json, random, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); s0 = int(a.seed_start); pert = a.pert
    lam = 8.0
    svc = 5.0 / 60.0
    c = 1
    if pert == "lam_up": lam *= 1.1
    elif pert == "mu_up": svc /= 1.1
    elif pert == "c_up": c = 2
    warm = 0.25 * H
    per_L, per_W, per_bf, per_pl, per_pw, seed_list = [], [], [], [], [], []
    tot_L = tot_W = tot_bf = tot_pl = tot_pw = 0.0
    tot_arr = tot_dep = tot_blk = 0.0
    for k in range(n_seeds):
        seed = s0 + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        ev = []
        heapq.heappush(ev, (next_arr, 0, None))
        cnt = 0
        N = 0
        queue = []
        srv = [0.0] * c
        heapq.heapify(srv)
        last_t = 0.0
        L_area = 0.0
        busy_area_m1 = 0.0
        busy_area_occ = 0.0
        arr_w = dep_w = blk_w = 0
        wait_sum = 0.0
        waited = 0
        dep_time_sum = 0.0
        while ev:
            e = heapq.heappop(ev)
            t = e[0]
            if t > H:
                break
            seg_s = max(last_t, warm); seg_e = min(t, H)
            if seg_e > seg_s:
                dt = seg_e - seg_s
                L_area += N * dt
                busy_area_m1 += min(N, 1) * dt
                busy_area_occ += (1 if N > 0 else 0) * dt
            if e[1] == 0:
                svc_t = svc
                heapq.heappush(queue, (t, svc_t))
                N += 1
                if t >= warm:
                    arr_w += 1
                while queue and srv[0] <= t:
                    a_t, s_t = heapq.heappop(queue)
                    free = heapq.heappop(srv)
                    start = max(t, free)
                    d_t = start + s_t
                    cnt += 1
                    heapq.heappush(srv, d_t)
                    heapq.heappush(ev, (d_t, 1, (a_t, start, d_t)))
                cnt += 1
                nt = t + rng.expovariate(lam)
                heapq.heappush(ev, (nt, 0, None))
            else:
                a_t, start, d_t = e[2]
                N -= 1
                if d_t >= warm and a_t >= warm:
                    dep_w += 1
                    dep_time_sum += d_t - a_t
                    if start > a_t:
                        waited += 1
                        wait_sum += start - a_t
                if N < len(srv) and N < c:
                    pass
            last_t = t
        win = H - warm
        if win <= 0:
            win = H
        L = L_area / win
        bf = busy_area_m1 / win
        occ = busy_area_occ / win
        Wm = (dep_time_sum / dep_w * 60.0) if dep_w > 0 else 0.0
        pw = (waited / arr_w) if arr_w > 0 else 0.0
        pl = 0.0
        per_L.append(L); per_W.append(Wm); per_bf.append(bf)
        per_pl.append(pl); per_pw.append(pw)
        tot_L += L; tot_W += Wm; tot_bf += bf
        tot_pl += pl; tot_pw += pw
        tot_arr += arr_w; tot_dep += dep_w; tot_blk += blk_w
    n = n_seeds
    out = {
        "L": tot_L / n,
        "W": tot_W / n,
        "busy_frac": tot_bf / n,
        "busy_util": tot_bf / n,
        "busy_occupied": tot_bf / n,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "win": H - warm,
        "arr": tot_arr / n,
        "blk": tot_blk / n,
        "dep": tot_dep / n,
        "dep_rate": (tot_dep / n) / (H - warm),
        "lam_eff": lam,
        "p_loss": tot_pl / n,
        "p_wait": tot_pw / n,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
