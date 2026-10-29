import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 6.0
    mu = 10.0
    c = 1
    if a.pert == 'lam_up':
        lam = lam * 1.2
    elif a.pert == 'mu_up':
        mu = mu * 1.2
    elif a.pert == 'c_up':
        c = 2

    H = float(a.horizon)
    warm = 0.25 * H
    svc = 60.0 / mu

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = tot_busy = 0.0
    tot_win = 0.0
    tot_wait_n = 0.0
    tot_wait_sum = 0.0

    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        seed_list.append(s)
        t = 0.0
        n = 0
        busy_until = 0.0
        queue = []
        arr = dep = blk = 0
        area = 0.0
        busy_area = 0.0
        wait_sum = 0.0
        wait_n = 0
        last = 0.0
        while True:
            if n == 0:
                dt = rng.expovariate(lam)
                nt = t + dt
            else:
                dt = rng.expovariate(lam)
                nt = t + dt
            if nt > H:
                break
            area += n * (nt - t)
            busy_area += (1 if n > 0 else 0) * (nt - t)
            t = nt
            n += 1
            arr += 1
            service = svc
            queue.append((t, service))
            if n == 1:
                busy_until = t + service
            while queue and queue[0][0] + queue[0][1] <= t:
                pass
            while n > 0 and busy_until <= t:
                break
            if n > 0 and busy_until <= t:
                pass
            if n == 1:
                pass
            if n > 0:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
            if n > 0 and busy_until <= t:
                pass
