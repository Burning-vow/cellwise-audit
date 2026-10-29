import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=100.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 10.0
    c = 2
    if a.pert == 'lam_up': lam *= 1.2
    elif a.pert == 'mu_up': mu *= 1.2
    elif a.pert == 'c_up': c = 3
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL=[]; pW=[]; pB=[]; pPL=[]; pPW=[]
    tot_arr=0.0; tot_dep=0.0; tot_blk=0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        servers = []
        arr_times = []
        dep_times = []
        blk_count = 0
        area_n = 0.0
        area_busy = 0.0
        area_q = 0.0
        wait_sum = 0.0
        wait_cnt = 0
        wait_events = 0
        arr_cnt = 0
        dep_cnt = 0
        last_t = 0.0
        next_arr = rng.expovariate(lam)
        while True:
            if servers:
                next_dep = min(servers)
            else:
                next_dep = float('inf')
            if next_arr < next_dep:
                nt = next_arr
            else:
                nt = next_dep
            if nt > H:
                dt = H - last_t
                area_n += n * dt
                area_busy += busy * dt
                area_q += len(queue) * dt
                last_t = H
                break
            dt = nt - last_t
            area_n += n * dt
            area_busy += busy * dt
            area_q += len(queue) * dt
            last_t = nt
            t = nt
            if next_arr <= next_dep:
                arr_cnt += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    servers.append(t + svc)
                    if t >= warm:
                        wait_sum += 0.0
                        wait_cnt += 1
                else:
                    queue.append((t, svc))
                    if t >= warm:
                        wait_events += 1
                n += 1
                next_arr = t + rng.expovariate(lam)
            else:
                servers.remove(next_dep)
                busy -= 1
                dep_cnt += 1
                if queue:
                    at, svc = queue.pop(0)
                    busy += 1
                    servers.append(t + svc)
                    w = t - at
                    if t >= warm:
                        wait_sum += w
                        wait_cnt += 1
                n -= 1
        win = H - warm
        L = area_n / H
        W = (area_n / max(1, arr_cnt)) * 60.0 if arr_cnt > 0 else 0.0
        bf = area_busy / (c * H)
        pw = wait_events / max(1, arr_cnt) if arr_cnt > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pPL.append(0.0); pPW.append(pw)
        tot_arr += arr_cnt; tot_dep += dep_cnt; tot_blk += blk_count
    ns = len(seeds)
    L = sum(pL)/ns; W = sum(pW)/ns; bf = sum(pB)/ns; pw = sum(pPW)/ns
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_wait': pw,
        'runtime_units': H, 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': H - warm,
        'arr': tot_arr/ns, 'blk': tot_blk/ns, 'busy_util': bf,
        'busy_occupied': bf, 'dep': tot_dep/ns,
        'dep_rate': (tot_dep/ns)/(H/60.0) if H > 0 else 0.0,
        'lam_eff': lam*60.0, 'p_loss': 0.0,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pPL, 'per_seed_p_wait': pPW
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
