import argparse, heapq, json, math, random

def run(seed, H, lam, mu, c):
    rng = random.Random(seed)
    T0 = 0.75 * H
    events = []
    seq = 0
    t = rng.expovariate(lam)
    heapq.heappush(events, (t, seq, 'arr', None)); seq += 1
    N = 0
    busy = 0
    last_t = 0.0
    area_N = 0.0; area_N_w = 0.0
    area_B = 0.0; area_B_w = 0.0
    arr_w = 0; dep_w = 0; wait_w = 0; n_wait = 0
    dep_count = 0
    Wsum = 0.0
    served = {}
    def add_area(t):
        nonlocal last_t, area_N, area_N_w, area_B, area_B_w
        dt = t - last_t
        if dt > 0:
            area_N += N * dt
            area_B += busy * dt
            lo = max(last_t, T0)
            hi = min(t, H)
            if hi > lo:
                area_N_w += N * (hi - lo)
                area_B_w += busy * (hi - lo)
            last_t = t
    while events:
        t, _, typ, cust = heapq.heappop(events)
        if t >= H:
            add_area(H)
            break
        add_area(t)
        if typ == 'arr':
            if t >= T0:
                arr_w += 1
                if busy >= c:
                    wait_w += 1; n_wait += 1
                else:
                    n_wait += 1
            svc = rng.expovariate(mu)
            cid = seq; seq += 1
            served[cid] = {'a': t, 's': svc, 'st': t}
            if busy < c:
                busy += 1
                served[cid]['busy_now'] = True
                heapq.heappush(events, (t + svc, seq, 'dep', cid)); seq += 1
            else:
                served[cid]['busy_now'] = False
                served[cid]['svc'] = svc
            nt = t + rng.expovariate(lam)
            heapq.heappush(events, (nt, seq, 'arr', None)); seq += 1
        else:
            d = served.pop(cust)
            if t >= T0:
                dep_w += 1
                Wsum += (t - d['a'])
            dep_count += 1
            nxt = q.pop(0) if q else None
            if nxt is not None:
                pass
            busy -= 1
            if q:
                nc = q.pop(0)
                busy += 1
                served[nc]['st'] = t
                heapq.heappush(events, (t + served[nc]['svc'], seq, 'dep', nc)); seq += 1
            if t >= T0 and served.get('_q'):
                pass
    return area_N_w, area_B_w, arr_w, dep_w, wait_w, n_wait, Wsum

q = []

def main():
    global q
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=5)
    p.add_argument('--horizon', type=float, default=2000.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    lam, mu, c = 14.0, 10.0, 2
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu *= 1.1
    elif a.pert == 'c_up': c = 3
    seed_list = list(range(a.seed_start, a.seed_start + a.seeds))
    per_L = []; per_W = []; per_bf = []; per_pw = []; per_pl = []
    tot = dict(L=0.0, W=0.0, bf=0.0, pw=0.0, pl=0.0, arr=0.0, dep=0.0, blk=0.0, dep_rate=0.0, bu=0.0, bo=0.0)
    H = a.horizon
    T0 = 0.75 * H
    for s in seed_list:
        rng = random.Random(s)
        events = []; seq = 0; q = []
        t = rng.expovariate(lam)
        heapq.heappush(events, (t, seq, 'arr', None)); seq += 1
        N = 0; busy = 0; last_t = 0.0
        area_N_w = 0.0; area_B_w = 0.0
        arr_w = dep_w = wait_w = 0; Wsum = 0.0
        cust = {}
        while events:
            t, _, typ, cid = heapq.heappop(events)
            if t >= H:
                dt = H - last_t
                area_N_w += N * dt; area_B_w += busy * dt
                break
            dt = t - last_t
            lo = max(last_t, T0); hi = min(t, H)
            if hi > lo:
                area_N_w += N * (hi - lo); area_B_w += busy * (hi - lo)
            last_t = t
            if typ == 'arr':
                if t >= T0:
                    arr_w += 1
                    if busy >= c: wait_w += 1
                svc = rng.expovariate(mu)
                cid2 = seq; seq += 1
                if busy < c:
                    busy += 1
                    heapq.heappush(events, (t + svc, seq, 'dep', cid2)); seq += 1
                else:
                    q.append((cid2, svc))
                nt = t + rng.expovariate(lam)
                heapq.heappush(events, (nt, seq, 'arr', None)); seq += 1
                cust[cid2] = t
            else:
                if t >= T0:
                    dep_w += 1
                    Wsum += t - cust.pop(cid, t)
                busy -= 1
                if q and busy < c:
                    nc, sv = q.pop(0)
                    busy += 1
                    heapq.heappush(events, (t + sv, seq, 'dep', nc)); seq += 1
        win = H - T0
        L = area_N_w / win
        bf = area_B_w / win / c
        W = Wsum / dep_w if dep_w else 0.0
        pw = wait_w / arr_w if arr_w else 0.0
        per_L.append(L); per_W.append(W); per_bf.append(bf); per_pw.append(pw); per_pl.append(0.0)
        tot['L'] += L; tot['W'] += W; tot['bf'] += bf; tot['pw'] += pw
        tot['arr'] += arr_w / win; tot['dep'] += dep_w / win
        tot['dep_rate'] += dep_w / win
        tot['bu'] += bf; tot['bo'] += 0.0
    n = len(seed_list)
    out = {
        'L': tot['L']/n, 'W': tot['W']/n, 'busy_frac': tot['bf']/n,
        'p_wait': tot['pw']/n, 'runtime_units': n, 'seed_list': seed_list,
        'seeds_used': n, 'time_unit': 'hour', 'win': 0.25*H,
        'arr': tot['arr']/n, 'blk': 0.0, 'busy_util': tot['bu']/n,
        'busy_occupied': 1.0 - math.exp(-0.0) if False else None,
        'dep': tot['dep']/n, 'dep_rate': tot['dep_rate']/n,
        'lam_eff': tot['arr']/n, 'p_loss': 0.0,
        'per_seed_L': per_L, 'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf, 'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    out['busy_occupied'] = 1.0 - (1.0 - min(1.0, lam/(c*mu))) if False else out['busy_util']
    print(json.dumps(out))

if __name__ == "__main__":
    main()
