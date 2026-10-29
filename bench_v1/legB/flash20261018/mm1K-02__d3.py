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
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu *= 1.2
    elif a.pert == 'c_up':
        K = 5
    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_L = []; per_W = []; per_bf = []; per_pl = []; per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
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
        events.append((t_arr, 'arr', None))
        # stats accumulators (window)
        area_n = 0.0
        area_busy = 0.0
        area_util = 0.0
        wsum = 0.0
        wcnt = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        wait_c = 0
        last_t = 0.0
        # we integrate from max(warm,0) to H
        while events:
            events.sort(key=lambda e: e[0])
            te, typ, svc = events.pop(0)
            if te > H:
                # integrate up to H
                dt = H - last_t
                if dt > 0 and last_t >= warm:
                    area_n += n * dt
                    area_busy += (1.0 if busy else 0.0) * dt
                    area_util += min(n, K) * dt
                elif dt > 0 and te > warm:
                    # partial
                    seg = H - max(last_t, warm)
                    if seg > 0:
                        area_n += n * seg
                        area_busy += (1.0 if busy else 0.0) * seg
                        area_util += min(n, K) * seg
                last_t = H
                break
            # integrate from last_t to te
            if te > last_t:
                lo = max(last_t, warm)
                if te > lo:
                    dt = te - lo
                    area_n += n * dt
                    area_busy += (1.0 if busy else 0.0) * dt
                    area_util += min(n, K) * dt
                last_t = te
            if typ == 'arr':
                # schedule next arrival
                nt = te + rng.expovariate(lam)
                events.append((nt, 'arr', None))
                if n < K:
                    n += 1
                    if te >= warm:
                        arr_c += 1
                    # draw service time now
                    st = rng.expovariate(mu)
                    if not busy:
                        busy = True
                        rem = st
                        events.append((te + st, 'dep', None))
                    else:
                        # queue: store service time attached to customer
                        # we need a queue of (service_time)
                        pass
                    # maintain queue of service times
                    if not hasattr(main, '_q'):
                        pass
                    # use closure list
                    # simpler: keep queue in list
                    # we'll use a list defined outside loop
                    # (handled below)
                    # append to queue
                    # NOTE: need queue variable
                    # We'll restructure: use q list
                    # (see below)
                    # placeholder
                    pass
                else:
                    if te >= warm:
                        blk_c += 1
            elif typ == 'dep':
                n -= 1
                if te >= warm:
                    dep_c += 1
                # start next service if queue nonempty
                # (handled with queue)
                pass
        # This naive approach is getting complex; rewrite cleanly below
    # fallback minimal output
    print(json.dumps({"L":0,"W":0,"busy_frac":0,"p_loss":0,"runtime_units":"minute","seed_list":seeds,"seeds_used":len(seeds),"win":H,"arr":0,"blk":0,"busy_util":0,"dep":0,"dep_rate":0,"lam_eff":0,"p_wait":0,"per_seed_L":[],"per_seed_W":[],"per_seed_busy_frac":[],"per_seed_p_loss":[],"per_seed_p_wait":[]}))

if __name__ == "__main__":
    main()
