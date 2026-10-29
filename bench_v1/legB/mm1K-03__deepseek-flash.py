import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 8.0
    mu = 10.0
    K = 4
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        K = K + 1

    H = a.horizon
    warm = 0.25 * H
    win = H - warm

    per_L = []
    per_W = []
    per_busy = []
    seed_list = []
    tot_arr = 0.0
    tot_blk = 0.0
    tot_dep = 0.0

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        n = 0
        busy = False
        cur_dep = 0.0
        queue = []
        area_n = 0.0
        area_b = 0.0
        arr_w = 0
        blk_w = 0
        dep_w = 0
        wait_sum = 0.0
        dep_times = []
        last = 0.0
        while True:
            if not busy:
                dt = rng.expovariate(lam)
                t_next = t + dt
            else:
                dt = rng.expovariate(lam)
                t_next = t + dt
            if t_next > H:
                area_n += n * (H - t)
                area_b += (1.0 if busy else 0.0) * (H - t)
                break
            area_n += n * (t_next - t)
            area_b += (1.0 if busy else 0.0) * (t_next - t)
            t = t_next
            if n < K:
                n += 1
                svc = rng.expovariate(mu)
                if t >= warm:
                    arr_w += 1
                if not busy:
                    busy = True
                    cur_dep = t + svc
                    if t >= warm:
                        wait_sum += 0.0
                        dep_times.append(cur_dep)
                else:
                    queue.append((t, svc))
            else:
                if t >= warm:
                    blk_w += 1
            if busy and t >= cur_dep:
                n -= 1
                busy = False
                if t >= warm:
                    dep_w += 1
                if queue:
                    at, svc = queue.pop(0)
                    busy = True
                    cur_dep = t + svc
                    if t >= warm:
                        wait_sum += (t - at)
                        dep_times.append(cur_dep)
        L = area_n / win if win > 0 else 0.0
        bf = area_b / win if win > 0 else 0.0
        W = (wait_sum / dep_w) if dep_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_busy.append(bf)
        tot_arr += arr_w
        tot_blk += blk_w
        tot_dep += dep_w

    seeds_used = a.seeds
    arr_avg = tot_arr / seeds_used
    blk_avg = tot_blk / seeds_used
    dep_avg = tot_dep / seeds_used
    p_loss = (blk_avg / (arr_avg + blk_avg)) if (arr_avg + blk_avg) > 0 else 0.0
    dep_rate = dep_avg / win if win > 0 else 0.0
    L = sum(per_L) / seeds_used
    W = sum(per_W) / seeds_used

    out = {
        'L': L,
        'W': W,
        'arr': arr_avg,
        'blk': blk_avg,
        'dep': dep_avg,
        'dep_rate': dep_rate,
        'p_loss': p_loss,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_busy,
        'runtime_units': 'hour',
        'seed_list': seed_list,
        'seeds_used': seeds_used,
        'time_unit': 'hour',
        'win': win
    }
    print(json.dumps(out))

main()
