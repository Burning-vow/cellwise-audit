import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam_base, mu_base = 4.0, 12.0
    if a.pert == "lam_up": lam_base *= 1.1
    elif a.pert == "mu_up": mu_base *= 1.1
    elif a.pert == "c_up": pass
    seeds_used = []
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    total_arr, total_dep, total_blk = 0.0, 0.0, 0.0
    win_len = a.horizon * 0.75
    for i in range(a.seeds):
        s = a.seed_start + i
        rng = random.Random(s)
        t = 0.0; n = 0; busy = False; next_arr = rng.expovariate(lam_base); next_dep = float('inf')
        area_n = 0.0; area_busy = 0.0; warmup_end = a.horizon * 0.25
        arr_cnt = dep_cnt = blk_cnt = wait_cnt = 0
        last_t = 0.0
        while t < a.horizon:
            if not busy and next_arr <= next_dep:
                dt = next_arr - t; t = next_arr
                if t >= warmup_end:
                    area_n += n * dt; area_busy += (1 if busy else 0) * dt
                n += 1; arr_cnt += 1
                svc = rng.expovariate(mu_base)
                busy = True; next_dep = t + svc
                next_arr = t + rng.expovariate(lam_base)
            elif busy and next_dep <= next_arr:
                dt = next_dep - t; t = next_dep
                if t >= warmup_end:
                    area_n += n * dt; area_busy += (1 if busy else 0) * dt
                n -= 1; dep_cnt += 1; busy = False
                next_dep = float('inf')
            else:
                dt = min(next_arr, next_dep) - t; t = min(next_arr, next_dep)
                if t >= warmup_end:
                    area_n += n * dt; area_busy += (1 if busy else 0) * dt
                if abs(t - next_arr) < 1e-9:
                    n += 1; arr_cnt += 1
                    svc = rng.expovariate(mu_base)
                    busy = True; next_dep = t + svc
                    next_arr = t + rng.expovariate(lam_base)
                else:
                    n -= 1; dep_cnt += 1; busy = False
                    next_dep = float('inf')
        eff_win = max(0.0, a.horizon - warmup_end)
        L_est = area_n / eff_win if eff_win > 0 else 0.0
        W_est = L_est / (dep_cnt / eff_win) if dep_cnt > 0 and eff_win > 0 else 0.0
        bf_est = area_busy / eff_win if eff_win > 0 else 0.0
        pl_est = blk_cnt / arr_cnt if arr_cnt > 0 else 0.0
        pw_est = wait_cnt / arr_cnt if arr_cnt > 0 else 0.0
        seeds_used.append(s)
        per_seed_L.append(L_est); per_seed_W.append(W_est); per_seed_busy_frac.append(bf_est)
        per_seed_p_loss.append(pl_est); per_seed_p_wait.append(pw_est)
        total_arr += arr_cnt; total_dep += dep_cnt; total_blk += blk_cnt
    N = len(seeds_used)
    avg_L = sum(per_seed_L)/N; avg_W = sum(per_seed_W)/N; avg_bf = sum(per_seed_busy_frac)/N
    avg_pl = sum(per_seed_p_loss)/N; avg_pw = sum(per_seed_p_wait)/N
    avg_arr = total_arr/N; avg_dep = total_dep/N; avg_blk = total_blk/N
    dep_rate = avg_dep / win_len * 60.0 if win_len > 0 else 0.0
    lam_eff = dep_rate / 60.0 if win_len > 0 else 0.0
    out = {
        "L": round(avg_L, 6), "W": round(avg_W, 6), "busy_frac": round(avg_bf, 6),
        "p_wait": round(avg_pw, 6), "runtime_units": "hour", "seed_list": seeds_used,
        "seeds_used": N, "time_unit": "hour", "win": round(win_len, 6),
        "arr": round(avg_arr, 6), "blk": round(avg_blk, 6), "busy_util": round(avg_bf, 6),
        "dep": round(avg_dep, 6), "dep_rate": round(dep_rate, 6), "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_pl, 6), "per_seed_L": [round(x,6) for x in per_seed_L],
        "per_seed_W": [round(x,6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x,6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x,6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x,6) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
