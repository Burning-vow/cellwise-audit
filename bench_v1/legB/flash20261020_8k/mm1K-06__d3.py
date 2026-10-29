import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 9.0 / 60.0
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
    tot_areaN = tot_areaBusy = 0.0
    tot_wait = tot_waited = 0.0
    tot_dep_time = 0.0
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        next_arr = rng.expovariate(lam)
        svc_end = float('inf')
        areaN = 0.0
        areaBusy = 0.0
        arr_c = dep_c = blk_c = 0
        wait_sum = 0.0
        waited_c = 0
        dep_time_sum = 0.0
        while True:
            if next_arr <= svc_end:
                tnext = next_arr
                ev = 'arr'
            else:
                tnext = svc_end
                ev = 'dep'
            if tnext > H:
                dt = H - t
                if t >= warm:
                    areaN += n * dt
                    areaBusy += busy * dt
                t = H
                break
            dt = tnext - t
            if t >= warm:
                areaN += n * dt
                areaBusy += busy * dt
            t = tnext
            if ev == 'arr':
                if t >= warm:
                    arr_c += 1
                if n < K:
                    n += 1
                    if n == 1:
                        busy = 1
                    svc = rng.expovariate(mu)
                    if n == 1:
                        svc_end = t + svc
                    else:
                        pass
                    if n == 1:
                        pass
                    if n >= 1 and busy == 1 and svc_end == float('inf'):
                        svc_end = t + svc
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
                        pass
                    if n == 1:
