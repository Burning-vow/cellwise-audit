import json, argparse, heapq, random, math

def run_seed(seed, lam, mu, c_cap, horizon, warm):
    rng = random.Random(seed)
    t = 0.0; q = []  # events (time, type, idx)
    eid = 0
    heapq.heappush(q, (rng.expovariate(lam), 'arr', eid)); eid += 1
    n = 0; busy_until = None
    area_L = 0.0; last = 0.0
    stats = dict(arr=0, dep=0, blk=0, busy_area=0.0, wait_sum=0.0, waited=0, served=0)
    arrivals = {}
    while q:
        t, typ, idx = heapq.heappop(q)
        if t > horizon: break
        if t >= warm:
            area_L += n * (t - last)
            stats['busy_area'] += (1 if n > 0 else 0) * (t - last)
        last = t
        if typ == 'arr':
            if t >= warm: stats['arr'] += 1
            if n < c_cap:
                n += 1
                st = rng.expovariate(mu)
                arrivals[idx] = (t, st)
                if n == 1:
                    heapq.heappush(q, (t + st, 'dep', idx))
                else:
                    pass
                if idx not in serving: pass
            else:
                if t >= warm: stats['blk'] += 1
            heapq.heappush(q, (t + rng.expovariate(lam), 'arr', eid)); eid += 1
        else:
            n -= 1
            a, st = arrivals.pop(idx)
            if t >= warm:
                stats['dep'] += 1
                stats['wait_sum'] += (t - a - st) if st < math.inf else 0
                stats['waited'] += 1
                stats['served'] += 1
            if n > 0:
                nx = min(arrivals.keys(), key=lambda k: arrivals[k][0])
                heapq.heappush(q, (t + arrivals[nx][1], 'dep', nx))
                arrivals[nx] = (arrivals[nx][0], math.inf)
    if horizon > last:
        area_L += n * (horizon - last)
        stats['busy_area'] += (1 if n > 0 else 0) * (horizon - last)
    win = horizon - warm
    L = area_L / win
    dep = stats['dep']; arr = stats['arr']; blk = stats['blk']
    p_loss = blk / (arr + blk) if (arr + blk) > 0 else 0.0
    p_wait = stats['waited'] / dep if dep > 0 else 0.0
    W = stats['wait_sum'] / dep if dep > 0 else 0.0
    busy = stats['busy_area'] / win
    return dict(L=L, W=W, busy_frac=busy, p_loss=p_loss, p_wait=p_wait,
                arr=arr, dep=dep, blk=blk, dep_rate=dep / win)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu, cap = 9.0, 10.0, 4
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': cap += 1
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    warm = 0.25 * a.horizon
    res = [run_seed(s, lam, mu, cap, a.horizon, warm) for s in seeds]
    k = len(res)
    out = {
        'L': sum(r['L'] for r in res) / k,
        'W': sum(r['W'] for r in res) / k,
        'busy_frac': sum(r['busy_frac'] for r in res) / k,
        'p_loss': sum(r['p_loss'] for r in res) / k,
        'busy_util': sum(r['busy_frac'] for r in res) / k,
        'busy_occupied': sum(r['busy_frac'] for r in res) / k,
        'p_wait': sum(r['p_wait'] for r in res) / k,
        'arr': sum(r['arr'] for r in res) / k,
        'dep': sum(r['dep'] for r in res) / k,
        'blk': sum(r['blk'] for r in res) / k,
        'dep_rate': sum(r['dep_rate'] for r in res) / k,
        'lam_eff': sum(r['dep_rate'] for r in res) / k,
        'runtime_units': a.horizon,
        'seed_list': seeds,
        'seeds_used': k,
        'time_unit': 'hour',
        'win': a.horizon - warm,
        'per_seed_L': [r['L'] for r in res],
        'per_seed_W': [r['W'] for r in res],
        'per_seed_busy_frac': [r['busy_frac'] for r in res],
        'per_seed_p_loss': [r['p_loss'] for r in res],
        'per_seed_p_wait': [r['p_wait'] for r in res],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
