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
        # event list: (time, type, service_time)
        events = []
        # schedule first arrival
        t_arr = rng.expovariate(lam)
        events.append((t_arr, 'arr', 0.0))
        # stats
        area_n = 0.0; area_busy = 0.0; area_occ = 0.0
        wsum = 0.0; wcnt = 0
        arr_c = 0; dep_c = 0; blk_c = 0
        wait_c = 0
        last_t = 0.0
        while events:
            events.sort(key=lambda e: e[0])
            te, typ, svc = events.pop(0)
            if te > H:
                # integrate to H
                dt = H - last_t
                if dt > 0:
                    if last_t >= warm:
                        area_n += n * dt
                        area_busy += (1.0 if busy else 0.0) * dt
                        area_occ += (1.0 if n > 0 else 0.0) * dt
                break
            dt = te - last_t
            if dt > 0 and last_t >= warm:
                area_n += n * dt
                area_busy += (1.0 if busy else 0.0) * dt
                area_occ += (1.0 if n > 0 else 0.0) * dt
            last_t = te
            if typ == 'arr':
                arr_c += 1
                if n < K:
                    n += 1
                    if not busy:
                        busy = True
                        rem = svc
                        events.append((te + rem, 'dep', 0.0))
                    else:
                        # queue: store service time with customer
                        pass
                    # store service time for this customer
                    # we need per-customer service times; use a queue
                    # simpler: maintain list of pending service times
                    # We'll use a list attached to arrivals
                    # Actually need to track: when customer starts service, use their svc
                    # Use a queue of service times
                    # We'll restructure: keep queue of svc times
                    # Since we already appended dep for busy case, need queue
                    # Let's use a list
                    # (implemented below via q)
                    pass
                else:
                    blk_c += 1
                # schedule next arrival
                events.append((te + rng.expovariate(lam), 'arr', 0.0))
            elif typ == 'dep':
                n -= 1
                dep_c += 1
                if n > 0:
                    # next customer starts service
                    # need their service time
                    pass
                else:
                    busy = False
        # This approach is getting messy; rewrite cleanly below
    # placeholder
    print(json.dumps({}))

if __name__ == "__main__":
    main()
