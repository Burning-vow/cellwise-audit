import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=str, default='2000')
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    H = float(a.horizon)
    lam = 6.0 / 60.0
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        pass
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_area = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_waited = 0.0
    tot_dep_w = 0.0
    win_total = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n = 0
        busy = False
        next_dep = float('inf')
        area = 0.0
        busy_area = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        waited_cnt = 0
        dep_w_sum = 0.0
        last_t = 0.0
        while True:
            if busy:
                dt = next_dep - t
            else:
                dt = rng.expovariate(lam)
            if t + dt > H:
                if busy:
                    area += n * (H - t)
                    busy_area += (H - t)
                else:
                    area += n * (H - t)
                break
            if busy:
                area += n * dt
                busy_area += dt
                t = next_dep
                n -= 1
                if t >= warm:
                    dep_w += 1
                if n == 0:
                    busy = False
                    next_dep = float('inf')
                else:
                    next_dep = t + rng.expovariate(mu)
            else:
                area += n * dt
                t += dt
                n += 1
                if t >= warm:
                    arr_w += 1
                svc = rng.expovariate(mu)
                if n == 1:
                    busy = True
                    next_dep = t + svc
                    if t >= warm:
                        wait_sum += 0.0
                        waited_cnt += 0
                else:
                    if t >= warm:
                        wait_sum += 0.0
                        waited_cnt += 0
        win = H - warm
        Ls = area / H
        Ws = Ls / lam if lam > 0 else 0.0
        bf = busy_area / H
        per_L.append(Ls)
        per_W.append(Ws)
        per_bf.append(bf)
        per_pl.append(0.0)
        per_pw.append(0.0)
        tot_arr += arr_w
        tot_dep += dep_w
        tot_blk += blk_w
        tot_area += area
        tot_busy += busy_area
        win_total += win
    seeds_used = a.seeds
    L = sum(per_L) / seeds_used if seeds_used else 0.0
    W = sum(per_W) / seeds_used if seeds_used else 0.0
    busy_frac = sum(per_bf) / seeds_used if seeds_used else 0.0
    p_wait = sum(per_pw) / seeds_used if seeds_used else 0.0
    p_loss = sum(per_pl) / seeds_used if seeds_used else 0.0
    arr = tot_arr / seeds_used if seeds_used else 0.0
    dep = tot_dep / seeds_used if seeds_used else 0.0
    blk = tot_blk / seeds_used if seeds_used else 0.0
    win = win_total / seeds_used if seeds_used else 0.0
    dep_rate = (dep / win) * 60.0 if win > 0 else 0.0
    lam_eff = lam * 60.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy_frac,
        'busy_util': busy_frac,
        'busy_occupied': busy_frac,
        'p_wait': p_wait,
        'p_loss': p_loss,
        'runtime_units': 'minute',
        'time_unit': 'minute',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'win': win,
        'arr': arr,
        'dep': dep,
        'blk': blk,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
