import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 6.0 / 60.0
    mu = 1.0 / 5.0
    K = 4
    if a.pert == 'lam_up': lam *= 1.2
    elif a.pert == 'mu_up': mu *= 1.2
    elif a.pert == 'c_up': K = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    pL=[]; pW=[]; pB=[]; pP=[]; pPW=[]
    tot_arr=0.0; tot_dep=0.0; tot_blk=0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        arr_t = rng.expovariate(lam)
        dep_t = float('inf')
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        last = 0.0
        arr_c = 0; dep_c = 0; blk_c = 0; wait_c = 0
        while True:
            nxt = min(arr_t, dep_t)
            if nxt > H: nxt = H
            dt = nxt - last
            if last >= warm:
                area_n += n * dt
                area_busy += (1.0 if busy else 0.0) * dt
                area_occ += min(n, K) * dt
            last = nxt
            if nxt >= H: break
            if arr_t <= dep_t:
                arr_c += 1
                if n >= K:
                    blk_c += 1
                else:
                    if n > 0: wait_c += 1
                    n += 1
                    if not busy:
                        busy = True
                        rem = rng.expovariate(mu)
                        dep_t = t + rem
                arr_t = t + rng.expovariate(lam)
            else:
                dep_c += 1
                n -= 1
                if n > 0:
                    rem = rng.expovariate(mu)
                    dep_t = t + rem
                else:
                    busy = False
                    dep_t = float('inf')
            t = nxt
        win = H - warm
        L = area_n / win if win > 0 else 0.0
        bf = area_busy / win if win > 0 else 0.0
        bu = area_occ / (K * win) if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = wait_c / arr_c if arr_c > 0 else 0.0
        W = L / (dep_c / win) if dep_c > 0 else 0.0
        pL.append(L); pW.append(W); pB.append(bf); pP.append(pl); pPW.append(pw)
        tot_arr += arr_c; tot_dep += dep_c; tot_blk += blk_c
    ns = len(seeds)
    win = H - warm
    L = sum(pL)/ns; W = sum(pW)/ns; bf = sum(pB)/ns; pl = sum(pP)/ns; pw = sum(pPW)/ns
    dep_rate = (tot_dep/ns) / win if win > 0 else 0.0
    out = {
        'L': L, 'W': W, 'busy_frac': bf, 'p_loss': pl,
        'runtime_units': 'minute', 'seed_list': seeds, 'seeds_used': ns,
        'time_unit': 'minute', 'win': win,
        'arr': tot_arr/ns, 'blk': tot_blk/ns, 'dep': tot_dep/ns,
        'busy_util': bf, 'busy_occupied': bf,
        'dep_rate': dep_rate, 'lam_eff': lam, 'p_wait': pw,
        'per_seed_L': pL, 'per_seed_W': pW, 'per_seed_busy_frac': pB,
        'per_seed_p_loss': pP, 'per_seed_p_wait': pPW,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
