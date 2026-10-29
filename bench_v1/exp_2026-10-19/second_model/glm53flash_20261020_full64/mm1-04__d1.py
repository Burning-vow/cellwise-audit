import argparse, json, heapq, random, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam, mu = 6.0, 12.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": mu *= 1.05

    seeds_used = max(1, a.seeds)
    seed_list = list(range(a.seed_start, a.seed_start + seeds_used))
    horizon = a.horizon
    warm = 0.25 * horizon
    win = horizon - warm

    per_L, per_W, per_bf, per_pw, per_pl = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_bu = tot_occ = 0.0
    L_sum = W_sum = wait_cnt_sum = wait_frac = 0.0

    for sd in seed_list:
        rng = random.Random(sd)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        dep_times = []
        ev = [(next_arr, 0)]
        area_N = 0.0
        busy = 0.0
        area_wait = 0.0
        cnt_wait = 0
        cnt_arr = cnt_dep = cnt_blk = 0
        waits = []
        prev_t = 0.0
        while True:
            if not ev:
                break
            te, kind = heapq.heappop(ev)
            if te > horizon:
                break
            if te >= warm and n > 0:
                area_N += n * (te - prev_t)
                busy += (1 if n >= 1 else 0) * (te - prev_t)
            elif te >= warm and n == 0:
                area_N += 0.0
            if te >= warm and n >= 2:
                area_wait += (n - 1) * (te - prev_t)
            prev_t = te
            if kind == 0:
                svc = rng.expovariate(mu)
                cnt_arr += 1
                if n == 0:
                    heapq.heappush(ev, (te + svc, 1, svc))
                    n = 1
                elif n == 1 and len(ev) and False:
                    pass
                else:
                    n += 1
                    heapq.heappush(ev, (te + svc, 1, svc))
                heapq.heappush(ev, (te + rng.expovariate(lam), 0))
            else:
                n -= 1
                cnt_dep += 1
                if n >= 1:
                    pass
        raise SystemExit
    print(json.dumps({}))

if __name__ == "__main__":
    main()
