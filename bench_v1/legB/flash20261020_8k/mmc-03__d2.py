import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    c = 2
    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3
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
    seeds = []
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seeds.append(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        arr_t = rng.expovariate(lam)
        area_n = 0.0
        area_b = 0.0
        area_q = 0.0
        wsum = 0.0
        wcnt = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        wait_c = 0
        last = 0.0
        while True:
            if n == 0:
                nt = arr_t
            elif busy < c and queue:
                nt = min(arr_t, queue[0][0])
            else:
                nt = arr_t
            if nt > H:
                dt = H - last
                area_n += n * dt
                area_b += busy * dt
                area_q += len(queue) * dt
                last = H
                break
            dt = nt - last
            area_n += n * dt
            area_b += busy * dt
            area_q += len(queue) * dt
            last = nt
            t = nt
            if t == arr_t:
                svc = rng.expovariate(mu)
                arr_c += 1
                n += 1
                if busy < c:
                    busy += 1
                    dep_t = t + svc
                    queue.append((dep_t, t, svc))
                else:
                    blk_c += 0
                    if len(queue) >= 0:
                        pass
                    queue.append((None, t, svc))
                    wait_c += 1
                arr_t = t + rng.expovariate(lam)
            else:
                dep_t, at, svc = queue.pop(0)
                busy -= 1
                n -= 1
                dep_c += 1
                if t >= warm:
                    wsum += (t - at)
                    wcnt += 1
                if queue:
                    nd, nat, nsvc = queue[0]
                    if nd is None:
                        queue[0] = (t + nsvc, nat, nsvc)
                        busy += 1
        win = H - warm
        L = area_n / H
        W = (area_n / max(arr_c, 1)) * 60.0 if arr_c > 0 else 0.0
        bf = area_b / (c * H)
        bu = bf
        bo = 1.0 - (1.0 - area_b / H) if False else area_b / H
        pw = wait_c / max(arr_c, 1)
        pl = blk_c / max(arr_c, 1)
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        per_bu.append(bu)
        per_bo.append(bo)
        per_arr.append(arr_c / H)
        per_dep.append(dep_c / H)
        per_blk.append(blk_c / H)
        per_dr.append(dep_c / H)
    ns = len(seeds)
    def avg(x):
        return sum(x) / len(x) if x else 0.0
    out = {
        'L': avg(per_L),
        'W': avg(per_W),
        'busy_frac': avg(per_bf),
        'p_wait': avg(per_pw),
        'runtime_units': H,
        'seed_list': seeds,
        'seeds_used': ns,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': avg(per_arr),
        'blk': avg(per_blk),
        'busy_util': avg(per_bu),
        'busy_occupied': avg(per_bo),
        'dep': avg(per_dep),
        'dep_rate': avg(per_dr) * 60.0,
        'lam_eff': lam,
        'p_loss': avg(per_pl),
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
