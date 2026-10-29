import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0
    mu = 5.0
    c = 2
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = c + 1
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    per_bu = []
    per_bo = []
    arrs = []
    deps = []
    blks = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        area_n = 0.0
        area_q = 0.0
        area_b = 0.0
        area_busy = 0.0
        area_occ = 0.0
        win_area_n = 0.0
        win_area_q = 0.0
        win_area_b = 0.0
        win_area_busy = 0.0
        win_area_occ = 0.0
        win_arr = 0
        win_dep = 0
        win_blk = 0
        win_wait = 0.0
        win_wait_n = 0
        win_t = 0.0
        last = 0.0
        events = []
        t_next = rng.expovariate(lam)
        while t < H:
            if t_next <= t:
                pass
            if not events or t_next < events[0][0]:
                dt = t_next - t
                if t >= warm:
                    win_area_n += n * dt
                    win_area_q += len(queue) * dt
                    win_area_b += busy * dt
                    win_area_occ += (1 if busy > 0 else 0) * dt
                    win_t += dt
                area_n += n * dt
                area_q += len(queue) * dt
                area_b += busy * dt
                area_occ += (1 if busy > 0 else 0) * dt
                t = t_next
                svc = rng.expovariate(mu)
                if t >= warm:
                    win_arr += 1
                if busy < c:
                    busy += 1
                    events.append((t + svc, svc))
                    events.sort()
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        win_blk += 1
                n += 1
                t_next = t + rng.expovariate(lam)
            else:
                te, svc = events.pop(0)
                dt = te - t
                if t >= warm:
                    win_area_n += n * dt
                    win_area_q += len(queue) * dt
                    win_area_b += busy * dt
                    win_area_occ += (1 if busy > 0 else 0) * dt
                    win_t += dt
                area_n += n * dt
                area_q += len(queue) * dt
                area_b += busy * dt
                area_occ += (1 if busy > 0 else 0) * dt
                t = te
                n -= 1
                busy -= 1
                if t >= warm:
                    win_dep += 1
                if queue:
                    at, sv = queue.pop(0)
                    busy += 1
                    events.append((t + sv, sv))
                    events.sort()
                    if t >= warm:
                        win_wait += (t - at) + sv
                        win_wait_n += 1
        if win_t <= 0:
            win_t = 1e-9
        L = win_area_n / win_t
        W = (win_wait / win_wait_n) if win_wait_n > 0 else 0.0
        bf = win_area_b / win_t / c
        bu = bf
        bo = win_area_occ / win_t
        pl = (win_blk / win_arr) if win_arr > 0 else 0.0
        pw = (win_blk / win_arr) if win_arr > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        per_bu.append(bu)
        per_bo.append(bo)
        arrs.append(win_arr)
        deps.append(win_dep)
        blks.append(win_blk)
    ns = len(per_L)
    L = sum(per_L) / ns
    W = sum(per_W) / ns
    bf = sum(per_bf) / ns
    bu = sum(per_bu) / ns
    bo = sum(per_bo) / ns
    pl = sum(per_pl) / ns
    pw = sum(per_pw) / ns
    arr = sum(arrs) / ns
    dep = sum(deps) / ns
    blk = sum(blks) / ns
    win = H - warm
    dep_rate = dep / win
    lam_eff = arr / win
    out = {
        'L': L,
        'W': W,
        'busy_frac': bf,
        'busy_util': bu,
        'busy_occupied': bo,
        'p_wait': pw,
        'p_loss': pl,
        'runtime_units': H,
        'seed_list': list(range(a.seed_start, a.seed_start + a.seeds)),
        'seeds_used': ns,
        'time_unit': 'hour',
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
