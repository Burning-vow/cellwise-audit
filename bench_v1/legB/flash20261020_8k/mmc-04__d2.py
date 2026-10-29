import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 10.0
    mu = 6.0
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
    per_arr = []
    per_dep = []
    per_blk = []
    per_dr = []
    per_le = []
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seeds.append(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        area_n = 0.0
        area_busy = 0.0
        area_q = 0.0
        arr_w = 0
        dep_w = 0
        blk_w = 0
        wait_sum = 0.0
        wait_cnt = 0
        waitq_cnt = 0
        arr_cnt = 0
        t_next = rng.expovariate(lam)
        while t < H:
            if n == 0:
                dt = t_next - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area_n += n * dt
                    area_busy += busy * dt
                    area_q += len(queue) * dt
                t += dt
                if t >= H:
                    break
                n += 1
                arr_cnt += 1
                if t >= warm:
                    arr_w += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    dep_t = t + svc
                    queue.append((dep_t, svc, t))
                else:
                    queue.append((None, svc, t))
                t_next = t + rng.expovariate(lam)
            else:
                dt = t_next - t
                if t + dt > H:
                    dt = H - t
                if t >= warm:
                    area_n += n * dt
                    area_busy += busy * dt
                    area_q += len(queue) * dt
                t += dt
                if t >= H:
                    break
                n += 1
                arr_cnt += 1
                if t >= warm:
                    arr_w += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    queue.append((t + svc, svc, t))
                else:
                    queue.append((None, svc, t))
                t_next = t + rng.expovariate(lam)
            while queue and queue[0][0] is not None and queue[0][0] <= t:
                dep_t, svc, at = queue.pop(0)
                busy -= 1
                n -= 1
                if dep_t >= warm:
                    dep_w += 1
                    wait_sum += dep_t - at
                    wait_cnt += 1
                if queue and queue[0][0] is None:
                    _, svc2, at2 = queue.pop(0)
                    busy += 1
                    queue.insert(0, (t + svc2, svc2, at2))
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        W = wait_sum / wait_cnt if wait_cnt > 0 else 0.0
        bf = area_busy / (c * win) if win > 0 else 0.0
        bu = bf
        bo = bf
        pl = blk_w / arr_w if arr_w > 0 else 0.0
        pw = waitq_cnt / arr_w if arr_w > 0 else 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        per_bu.append(bu)
        per_bo.append(bo)
        per_arr.append(arr_w)
        per_dep.append(dep_w)
        per_blk.append(blk_w)
        per_dr.append(dep_w / win if win > 0 else 0.0)
        per_le.append(arr_w / win if win > 0 else 0.0)
    ns = len(per_L)
    out = {
        'L': sum(per_L) / ns,
        'W': sum(per_W) / ns,
        'busy_frac': sum(per_bf) / ns,
        'p_wait': sum(per_pw) / ns,
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': H - warm,
        'arr': sum(per_arr) / ns,
        'blk': sum(per_blk) / ns,
        'busy_util': sum(per_bu) / ns,
        'busy_occupied': sum(per_bo) / ns,
        'dep': sum(per_dep) / ns,
        'dep_rate': sum(per_dr) / ns,
        'lam_eff': sum(per_le) / ns,
        'p_loss': sum(per_pl) / ns,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
