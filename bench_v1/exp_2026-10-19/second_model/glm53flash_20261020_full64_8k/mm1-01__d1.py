import argparse, json, random, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--horizon", type=float, default=10000.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()

    lam, mu = 4.0, 10.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": pass

    horizon = a.horizon
    warm = 0.25 * horizon
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0

    for i in range(a.seeds):
        seed = a.seed_start + i
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        next_arr = rng.expovariate(lam)
        next_dep = math.inf
        last_t = 0.0
        area_n = 0.0
        busy_time = 0.0
        w_sum = 0.0
        n_arr = n_dep = n_blk = n_wait = 0
        n_win = 0

        while t < horizon:
            t_next = min(next_arr, next_dep)
            dt = t_next - t
            a0, b0 = max(last_t, warm), min(t_next, horizon)
            if a0 < b0:
                area_n += n * (b0 - a0)
                if n >= 1:
                    busy_time += (b0 - a0)
            t = t_next
            last_t = t_next
            if next_arr <= next_dep:
                svc = rng.expovariate(mu)
                if t > warm:
                    n_arr += 1
                    n_win += 1
                    if n == 0:
                        n_wait += 1
                        w_sum += svc
                        next_dep = t + svc
                        n = 1
                    else:
                        n += 1
                else:
                    if n == 0:
                        next_dep = t + svc
                    n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                if t > warm:
                    n_dep += 1
                n -= 1
                if n > 0:
                    next_dep = t + rng.expovariate(mu)
                else:
                    next_dep = math.inf
            if t >= horizon:
                break

        win = horizon - warm
        per_L.append(area_n / win)
        per_W.append(w_sum / n_dep if n_dep > 0 else 0.0)
        per_bf.append(busy_time / win)
        per_pl.append(0.0)
        per_pw.append(n_wait / n_arr if n_arr > 0 else 0.0)
        tot_arr += n_arr
        tot_dep += n_dep
        tot_blk += 0.0

    S = a.seeds
    res = {
        "L": sum(per_L) / S,
        "W": sum(per_W) / S,
        "busy_frac": sum(per_bf) / S,
        "p_wait": sum(per_pw) / S,
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": S,
        "time_unit": "hour",
        "win": horizon - 0.25 * horizon,
        "arr": tot_arr / S,
        "blk": tot_blk / S,
        "busy_util": sum(per_bf) / S,
        "busy_occupied": sum(per_bf) / S,
        "dep": tot_dep / S,
        "dep_rate": tot_dep / S / (horizon - 0.25 * horizon),
        "lam_eff": tot_dep / S / (horizon - 0.25 * horizon),
        "p_loss": 0.0,
        "per_seed_L": per_L,
        "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(res))

if __name__ == "__main__":
    main()
