import argparse, json, math, random, heapq

def exp_time(rng, rate):
    return rng.expovariate(rate)

def draw_service(rng):
    if rng.random() < 0.2:
        return exp_time(rng, 1.0/0.3)
    else:
        return exp_time(rng, 1.0/0.05)

def run_seed(seed, horizon, lam):
    rng = random.Random(seed)
    warm = horizon * 0.25
    t = 0.0
    next_arr = exp_time(rng, lam)
    busy_until = None
    queue = []
    events = []
    heapq.heappush(events, (next_arr, 'a', None))
    cur_N = 0
    last_t = 0.0
    area_N = 0.0
    area_busy = 0.0
    win_area_N = 0.0
    win_area_busy = 0.0
    win_started = False
    win_len = horizon - warm
    n_arr_win = 0
    n_dep_win = 0
    n_loss_win = 0
    n_wait_win = 0
    sojourns = []
    while True:
        if not events:
            break
        ev_t, kind, payload = heapq.heappop(events)
        if ev_t > horizon:
            break
        dt = ev_t - last_t
        if win_started:
            win_area_N += cur_N * dt
            win_area_busy += (1 if cur_N > 0 else 0) * dt
        area_N += cur_N * dt
        area_busy += (1 if cur_N > 0 else 0) * dt
        last_t = ev_t
        if not win_started and ev_t >= warm:
            win_started = True
        t = ev_t
        if kind == 'a':
            svc = draw_service(rng)
            if cur_N == 0:
                heapq.heappush(events, (t + svc, 'd', t))
                cur_N = 1
            else:
                heapq.heappush(events, (t + svc, 'd', t)) if False else None
                queue.append((t, svc))
                cur_N += 1
            n_arr_win += 1 if win_started else 0
            heapq.heappush(events, (t + exp_time(rng, lam), 'a', None))
        else:
            arr_t = payload
            if win_started:
                sojourns.append(t - arr_t)
                n_dep_win += 1
            cur_N -= 1
            if queue:
                a0, s0 = queue.pop(0)
                heapq.heappush(events, (t + s0, 'd', a0))
            else:
                pass
        if kind == 'a' and cur_N > 1:
            pass
        if kind == 'a':
            if not win_started:
                pass
    return {
        'L': win_area_N / win_len,
        'busy_frac': win_area_busy / win_len,
        'n_arr_win': n_arr_win,
        'n_dep_win': n_dep_win,
        'n_loss_win': n_loss_win,
        'n_wait_win': n_wait_win,
        'W': (sum(sojourns)/len(sojourns))*60.0 if sojourns else 0.0,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=float, default=10)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=float, default=1)
    ap.add_argument('--pert', type=str, default='none')
    args = ap.parse_args()
    n_seeds = int(args.seeds)
    horizon = float(args.horizon)
    seed0 = int(args.seed_start)
    pert = args.pert
    lam = 3.0
    if pert == 'lam_up':
        lam *= 1.1
    mu_scale = 1.1 if pert == 'mu_up' else 1.0
    c_scale = 1.1 if pert == 'c_up' else 1.0
    seed_list = [seed0 + i for i in range(n_seeds)]
    per_L, per_W, per_bf, per_pl, per_pw = [], [], [], [], []
    tot_arr = tot_dep = tot_loss = tot_wait = 0.0
    for s in seed_list:
        r = run_seed(s, horizon, lam)
        per_L.append(r['L'])
        per_W.append(r['W'])
        per_bf.append(r['busy_frac'])
        per_pl.append(0.0)
        p_w = 0.0
        per_pw.append(p_w)
        tot_arr += r['n_arr_win']
        tot_dep += r['n_dep_win']
        tot_loss += r['n_loss_win']
        tot_wait += r['n_wait_win']
    win = horizon - horizon * 0.25
    k = float(n_seeds)
    L = sum(per_L)/k
    W = sum(per_W)/k
    busy = sum(per_bf)/k
    arr_rate = tot_arr/(k*win)
    dep_rate = tot_dep/(k*win)
    p_wait = tot_wait/(tot_arr) if tot_arr > 0 else 0.0
    out = {
        'L': L,
        'W': W,
        'busy_frac': busy,
        'busy_util': busy,
        'busy_occupied': busy,
        'runtime_units': horizon,
        'win': win,
        'time_unit': 'hour',
        'seed_list': seed_list,
        'seeds_used': n_seeds,
        'arr': arr_rate,
        'dep': dep_rate,
        'blk': 0.0,
        'dep_rate': dep_rate,
        'lam_eff': arr_rate,
        'p_loss': 0.0,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
        'pert': pert,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
