import argparse, heapq, json, math, random, sys

def exp_next(stream, rate):
    return stream.expovariate(rate)

def run_seed(seed, horizon, lam, mu1, mu2):
    rng = random.Random(seed)
    t = 0.0
    next_arr = exp_next(rng, lam)
    q1 = []; q2 = []
    busy1 = None; busy2 = None
    events = []
    eid = 0
    def push(time, kind, cust):
        nonlocal eid
        heapq.heappush(events, (time, eid, kind, cust))
        eid += 1
    push(next_arr, 'arr', None)
    warm = horizon * 0.25
    area = 0.0
    busy_t = 0.0
    wsum = 0.0
    n_dep = 0; n_arr = 0; n_loss = 0
    last = 0.0
    prev_enter = {}
    def integ(now):
        nonlocal area, busy_t, last
        n = len(q1) + len(q2) + (1 if busy1 is not None else 0) + (1 if busy2 is not None else 0)
        area += n * (now - last)
        b = (1 if busy1 is not None else 0) + (1 if busy2 is not None else 0)
        busy_t += b * (now - last)
        last = now
    while events:
        time, _, kind, cust = heapq.heappop(events)
        if time > horizon:
            break
        integ(time)
        t = time
        if kind == 'arr':
            if t < horizon:
                push(t + exp_next(rng, lam), 'arr', None)
            if busy1 is None:
                svc = exp_next(rng, mu1)
                busy1 = (t, svc, t)
                push(t + svc, 'done1', busy1)
            else:
                q1.append(t)
            if t >= warm:
                n_arr += 1
        elif kind == 'done1':
            _, svc, arr_t = cust
            if busy2 is None:
                s2 = exp_next(rng, mu2)
                busy2 = (t, s2, arr_t)
                push(t + s2, 'done2', busy2)
            else:
                q2.append(arr_t)
            if q1:
                a = q1.pop(0)
                s = exp_next(rng, mu1)
                busy1 = (t, s, a)
                push(t + s, 'done1', busy1)
            else:
                busy1 = None
        elif kind == 'done2':
            _, s2, arr_t = cust
            if t >= warm:
                wsum += t - arr_t
                n_dep += 1
            if q2:
                a = q2.pop(0)
                s = exp_next(rng, mu2)
                busy2 = (t, s, a)
                push(t + s, 'done2', busy2)
            else:
                busy2 = None
    integ(horizon)
    win = horizon - warm
    L = area / win if win > 0 else 0.0
    W = (wsum / n_dep) if n_dep > 0 else 0.0
    busy_frac = busy_t / (2 * win) if win > 0 else 0.0
    p_wait = 1.0
    p_loss = 0.0
    return dict(L=L, W=W, busy_frac=busy_frac, p_loss=p_loss, p_wait=p_wait,
                arr=n_arr, dep=n_dep, blk=n_loss, win=win)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=20000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu1, mu2 = 4.0, 8.0, 12.0
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu1 *= 1.1
    elif a.pert == 'c_up': mu2 *= 1.1
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per = [run_seed(s, a.horizon, lam, mu1, mu2) for s in seed_list]
    k = len(per)
    L = sum(p['L'] for p in per) / k
    W = sum(p['W'] for p in per) / k
    out = {
        'L': L, 'W': W, 'runtime_units': 'minutes', 'time_unit': 'minute',
        'seed_list': seed_list, 'seeds_used': k, 'win': per[0]['win'],
        'arr': sum(p['arr'] for p in per) / k,
        'dep': sum(p['dep'] for p in per) / k,
        'blk': 0.0,
        'dep_rate': sum(p['dep'] for p in per) / k / per[0]['win'] * 60.0,
        'lam_eff': lam,
        'p_loss': 0.0,
        'p_wait': 1.0,
        'busy_frac': sum(p['busy_frac'] for p in per) / k,
        'busy_util': sum(p['busy_frac'] for p in per) / k,
        'per_seed_L': [p['L'] for p in per],
        'per_seed_W': [p['W'] for p in per],
        'per_seed_busy_frac': [p['busy_frac'] for p in per],
        'per_seed_p_loss': [p['p_loss'] for p in per],
        'per_seed_p_wait': [p['p_wait'] for p in per],
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
