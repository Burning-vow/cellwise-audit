import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 10.0
    mu = 10.0
    c = 2
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        c = 3

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_busy_area = 0.0
    tot_win = 0.0
    tot_occ_area = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_times = []
        dep_times = []
        blk = 0
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        wait_sum = 0.0
        wait_cnt = 0
        wait_prob_cnt = 0
        arr_cnt = 0
        dep_cnt = 0
        last_t = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            if next_arr <= t:
                ev_t = next_arr
            elif servers:
                ev_t = min(servers)
            else:
                ev_t = next_arr
            if ev_t > H:
                ev_t = H
            dt = ev_t - last_t
            if last_t >= warm:
                area_n += n * dt
                area_busy += min(n, c) * dt
                area_occ += (1 if busy > 0 else 0) * dt
            last_t = ev_t
            t = ev_t
            if t >= H:
                break
            if next_arr <= t:
                arr_cnt += 1
                if last_t >= warm:
                    pass
                if busy < c:
                    busy += 1
                    st = rng.expovariate(mu)
                    servers.append(t + st)
                    if last_t >= warm:
                        wait_sum += 0.0
                        wait_cnt += 1
                else:
                    if last_t >= warm:
                        wait_prob_cnt += 1
                    queue.append(t)
                n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                servers.sort()
                ft = servers.pop(0)
                busy -= 1
                if queue:
                    at = queue.pop(0)
                    st = rng.expovariate(mu)
                    servers.append(t + st)
                    busy += 1
                    if last_t >= warm:
                        wait_sum += (t - at)
                        wait_cnt += 1
                n -= 1
                if last_t >= warm:
                    dep_cnt += 1
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = (wait_sum / wait_cnt) if wait_cnt > 0 else 0.0
        bf = area_busy / (c * win) if win > 0 else 0.0
        pw = wait_prob_cnt / arr_cnt if arr_cnt > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(pw)
        tot_arr += arr_cnt
        tot_dep += dep_cnt
        tot_blk += blk
        tot_busy_area += area_busy
        tot_occ_area += area_occ
        tot_win += win

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pw = sum(per_pw) / ns
    busy_util = bf
    busy_occupied = tot_occ_area / tot_win if tot_win > 0 else 0.0
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    dep_rate = dep / (tot_win / ns) if tot_win > 0 else 0.0
    lam_eff = lam * (1 - 0.0)
    p_loss = 0.0

    out = {
        "L": L, "W": W, "busy_frac": bf, "p_wait": pw,
        "runtime_units": H, "seed_list": seeds, "seeds_used": ns,
        "time_unit": "hour", "win": H - warm,
        "arr": arr, "blk": blk, "busy_util": busy_util,
        "busy_occupied": busy_occupied, "dep": dep, "dep_rate": dep_rate,
        "lam_eff": lam_eff, "p_loss": p_loss,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
