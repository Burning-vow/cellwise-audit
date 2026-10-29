import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0 / 60.0
    mu = 1.0 / 6.0
    c = 1
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_wait = tot_wait_n = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        servers = []
        area = 0.0
        busy_area = 0.0
        arr = dep = blk = 0
        wait_sum = 0.0
        wait_n = 0
        win_start = warm
        win_area = 0.0
        win_busy = 0.0
        win_arr = win_dep = win_blk = 0
        win_wait = 0.0
        win_wait_n = 0
        last_t = 0.0
        while True:
            dt = rng.expovariate(lam) if lam > 0 else float('inf')
            t_next = t + dt
            if t_next > H:
                break
            if t < win_start <= t_next:
                frac = (win_start - t) / dt if dt > 0 else 0.0
                win_area += (t_next - win_start) * n
                win_busy += (t_next - win_start) * min(n, c)
            else:
                if t >= win_start:
                    win_area += dt * n
                    win_busy += dt * min(n, c)
            t = t_next
            arr += 1
            if t >= win_start:
                win_arr += 1
            svc = rng.expovariate(mu) if mu > 0 else float('inf')
            if n < c:
                n += 1
                servers.append((t + svc, svc))
                if t >= win_start:
                    win_wait_n += 1
            else:
                blk += 1
                if t >= win_start:
                    win_blk += 1
            while servers and servers[0][0] <= t:
                servers.pop(0)
                n -= 1
                dep += 1
                if t >= win_start:
                    win_dep += 1
        # drain remaining
        while servers:
            t_dep = servers[0][0]
            if t_dep > H:
                if t < win_start < t_dep:
                    win_area += (t_dep - win_start) * n
                    win_busy += (t_dep - win_start) * min(n, c)
                elif t >= win_start:
                    win_area += (t_dep - t) * n
                    win_busy += (t_dep - t) * min(n, c)
                t = t_dep
            servers.pop(0)
            n -= 1
            dep += 1
            if t >= win_start:
                win_dep += 1
        win_len = H - win_start
        if win_len <= 0:
            win_len = 1e-9
        L = win_area / win_len
        bf = win_busy / (win_len * c)
        W = L / (win_dep / win_len) if win_dep > 0 else 0.0
        pl = win_blk / win_arr if win_arr > 0 else 0.0
        pw = (win_arr - win_blk - win_wait_n) / win_arr if win_arr > 0 else 0.0
        pw = max(0.0, min(1.0, pw))
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += win_arr
        tot_dep += win_dep
        tot_blk += win_blk
        tot_area += win_area
        tot_busy += win_busy
        tot_win += win_len

    ns = len(seeds)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = tot_arr / ns
    dep = tot_dep / ns
    blk = tot_blk / ns
    win = tot_win / ns
    dep_rate = dep / win if win > 0 else 0.0
    lam_eff = arr / win if win > 0 else 0.0
    busy_util = bf
    busy_occupied = bf

    out = {
        "L": L, "W": W, "busy_frac": bf,
        "runtime_units": H, "seed_list": seeds, "seeds_used": ns,
        "time_unit": "minute", "win": win,
        "arr": arr, "blk": blk, "busy_util": busy_util,
        "busy_occupied": busy_occupied,
        "dep": dep, "dep_rate": dep_rate, "lam_eff": lam_eff,
        "p_loss": pl, "p_wait": pw,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
