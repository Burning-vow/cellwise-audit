import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 6.0
    K = 4
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        K = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    tot_arr = 0.0; tot_dep = 0.0; tot_blk = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = False
        rem = 0.0
        # event list: (time, type, patient)
        # type 0 arrival, 1 departure
        events = []
        # schedule first arrival
        t_arr = rng.expovariate(lam)
        events.append((t_arr, 0, None))
        # stats
        area_n = 0.0
        area_busy = 0.0
        area_occ = 0.0
        win_arr = 0; win_dep = 0; win_blk = 0
        win_wait_sum = 0.0; win_wait_cnt = 0
        last_t = 0.0
        while events:
            events.sort(key=lambda e: e[0])
            te, typ, pat = events.pop(0)
            if te > H:
                # integrate to H
                dt = H - last_t
                if last_t >= warm:
                    area_n += n * dt
                    area_busy += (1.0 if busy else 0.0) * dt
                    area_occ += (1.0 if n > 0 else 0.0) * dt
                last_t = H
                break
            dt = te - last_t
            if last_t >= warm:
                area_n += n * dt
                area_busy += (1.0 if busy else 0.0) * dt
                area_occ += (1.0 if n > 0 else 0.0) * dt
            last_t = te
            if typ == 0:
                if te >= warm:
                    win_arr += 1
                if n < K:
                    n += 1
                    svc = rng.expovariate(mu)
                    pat = {'arr': te, 'svc': svc}
                    if not busy:
                        busy = True
                        rem = svc
                        events.append((te + svc, 1, pat))
                    else:
                        # queue: will be handled when current departs
                        pass
                    # store waiting patients in a simple list attached via events? 
                    # We'll manage queue via a list
                    if 'queue' not in dir():
                        pass
                else:
                    if te >= warm:
                        win_blk += 1
            else:
                # departure
                if te >= warm:
                    win_dep += 1
                    w = te - pat['arr'] - pat['svc']
                    win_wait_sum += w
                    win_wait_cnt += 1
                n -= 1
                # find next waiting patient
                # We need a queue; rebuild approach: keep queue list
                # Since we didn't store queue, we need to fix: use a list
                pass
        # This approach is flawed; rewrite with queue
    # placeholder
    print(json.dumps({}))

if __name__ == '__main__':
    main()
