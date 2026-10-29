import argparse, json, heapq, math, random

def run(seed, lam, mu, c, horizon):
    rng = random.Random(seed)
    t = 0.0; n = 0; depq = []
    arr_t = 0.0; next_arr = rng.expovariate(lam)
    stats = dict(Larea=0.0, Barea=0.0, occ_area=0.0, wait_area=0.0, arr=0, dep=0, pwait=0, pwait_den=0, wait_sum=0.0, wait_n=0)
    warm = horizon * 0.25
    pend = []
    while True:
        dep_t = depq[0] if depq else float('inf')
        a_t = arr_t + next_arr if t >= 0 or True else 0
        nt = min(a_t, dep_t)
        if nt > horizon: nt = horizon
        if t >= warm:
            stats['Larea'] += n * (nt - t)
            stats['Barea'] += min(n, c) * (nt - t)
            stats['occ_area'] += (1.0 if n > 0 else 0.0) * (nt - t)
        t = nt
        if t >= horizon: break
        if a_t <= dep_t:
            st = rng.expovariate(mu)
            a_t = t
            inwin = t >= warm
            if inwin: stats['arr'] += 1
            if n < c:
                n += 1
                heapq.heappush(depq, t + st)
                if inwin:
                    stats['wait_sum'] += 0.0; stats['wait_n'] += 1
                    stats['pwait_den'] += 1
            else:
                pend.append((t, st))
                if inwin:
                    stats['pwait'] += 1; stats['pwait_den'] += 1
            next_arr = rng.expovariate(lam)
            arr_t = t
        else:
            heapq.heappop(depq)
            n -= 1
            if pend:
                at, st = pend.pop(0)
                if t >= warm:
                    stats['wait_sum'] += (t - at); stats['wait_n'] += 1
                heapq.heappush(depq, t + st)
                n += 1
            if t >= warm: stats['dep'] += 1
    w = (horizon - warm)
    L = stats['Larea'] / w
    bf = stats['Barea'] / w / c
    occ = 1.0 - stats['occ_area'] / w
    W = (stats['wait_sum'] / stats['wait_n'] * 60.0) if stats['wait_n'] else 0.0
    pw = stats['pwait'] / stats['pwait_den'] if stats['pwait_den'] else 0.0
    return dict(L=L, W=W, busy_frac=bf, busy_util=bf, busy_occupied=occ, p_wait=pw,
                p_loss=0.0, blk=0, arr=stats['arr'] / 1, dep=stats['dep'],
                dep_rate=stats['dep'] / w, lam_eff=stats['arr'] / w, win=w)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=1000)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', default='none')
    a = ap.parse_args()
    lam, mu, c = 10.0, 6.0, 2
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': c += 1
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per = [run(s, lam, mu, c, a.horizon) for s in seed_list]
    m = lambda k: sum(p[k] for p in per) / len(per)
    out = {'L': m('L'), 'W': m('W'), 'busy_frac': m('busy_frac'), 'p_wait': m('p_wait'),
           'busy_util': m('busy_util'), 'busy_occupied': m('busy_occupied'),
           'p_loss': m('p_loss'), 'blk': m('blk'),
           'arr': m('arr'), 'dep': m('dep'), 'dep_rate': m('dep_rate'), 'lam_eff': m('lam_eff'),
           'per_seed_L': [p['L'] for p in per], 'per_seed_W': [p['W'] for p in per],
           'per_seed_busy_frac': [p['busy_frac'] for p in per],
           'per_seed_p_loss': [p['p_loss'] for p in per], 'per_seed_p_wait': [p['p_wait'] for p in per],
           'runtime_units': a.horizon, 'seed_list': seed_list, 'seeds_used': len(per),
           'time_unit': 'hour', 'win': per[0]['win']}
    print(json.dumps(out))

if __name__ == "__main__":
    main()
