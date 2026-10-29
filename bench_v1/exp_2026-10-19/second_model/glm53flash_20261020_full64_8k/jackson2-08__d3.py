import argparse, json, random, math, heapq

def run_seed(seed, H, params):
    rng = random.Random(seed)
    lam, mu1, mu2 = params
    t = 0.0
    warm = 0.25 * H
    t0 = warm
    area_L = 0.0
    last_t = 0.0
    def cur_L(): return n1 + n2 + (1 if busy1 else 0) + (1 if busy2 else 0)
    n1 = n2 = 0
    busy1 = busy2 = None
    served1 = 0
    dep = 0
    arr = 0
    lost = 0
    area_busy1 = 0.0
    area_busy2 = 0.0
    cust_in_q2 = []
    q2_departures = {}
    ev = []
    heapq.heappush(ev, (rng.expovariate(lam), 'arr', None))
    t1end = None
    t2end = None
    while ev:
        t, kind, cid = heapq.heappop(ev)
        if t > H:
            break
        if t >= warm:
            area_L += cur_L() * (t - last_t)
            area_busy1 += (1 if t1end is not None else 0) * (t - last_t)
            area_busy2 += (1 if t2end is not None else 0) * (t - last_t)
        last_t = t
        if kind == 'arr':
            arr += 1 if t >= warm else 0
            s1 = rng.expovariate(mu1)
            heapq.heappush(ev, (t + rng.expovariate(lam), 'arr', None))
            if t1end is None:
                t1end = t + s1
                heapq.heappush(ev, (t1end, 'done1', (t, s1)))
            else:
                n1 += 1
                q1.append((t, s1))
        elif kind == 'done1':
            at, s1 = cid
            heapq.heappush(ev, (t, 'enter2', (at, t)))
            if n1 > 0:
                a2, s1n = q1.pop(0)
                n1 -= 1
                t1end = t + s1n
                heapq.heappush(ev, (t1end, 'done1', (a2, s1n)))
            else:
                t1end = None
            heapq.heappush(ev, (t, 'enter2', (at, t)))
        elif kind == 'enter2':
            at, t1 = cid
            s2 = rng.expovariate(mu2)
            heapq.heappush(ev, (t, 'serve2', (at, t1, s2)))
        elif kind == 'serve2':
            at, t1, s2 = cid
            if t2end is None:
                t2end = t + s2
                heapq.heappush(ev, (t2end, 'done2', (at, t1, t, s2)))
            else:
                q2d.setdefault(id, None)
                q2.append((at, t1, s2))
                n2 += 1
        elif kind == 'done2':
            at, t1, ts, s2 = cid
            dep += 1 if t >= warm else 0
            if t >= warm:
                wait_sum.append((t - at))
            if n2 > 0:
                a, b, s = q2.pop(0)
                n2 -= 1
                t2end = t + s
                heapq.heappush(ev, (t2end, 'done2', (a, b, t, s)))
            else:
                t2end = None
    win = H - warm
    L = area_L / win
    W = (sum(wait_sum) / len(wait_sum) * 60) if wait_sum else 0.0
    bf1 = area_busy1 / win
    bf2 = area_busy2 / win
    return L, W, arr, dep, (bf1 + bf2) / 2, dep / win

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=10000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu1, mu2 = 6.0, 10.0, 12.0
    if a.pert == 'lam_up': lam *= 1.1
    elif a.pert == 'mu_up': mu1 *= 1.1; mu2 *= 1.1
    elif a.pert == 'c_up': pass
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    pL, pW, pbf, pdep = [], [], [], []
    for s in seeds:
        L, W, arr, dep, bf, dr = run_seed(s, a.horizon, (lam, mu1, mu2))
        pL.append(L); pW.append(W); pbf.append(bf); pdep.append(dep)
    out = {
        "L": sum(pL)/len(pL), "W": sum(pW)/len(pW),
        "runtime_units": a.horizon, "seed_list": seeds, "seeds_used": len(seeds),
        "time_unit": "hour", "win": a.horizon - 0.25*a.horizon,
        "arr": None, "dep": sum(pdep)/len(pdep), "blk": 0.0,
        "busy_frac": sum(pbf)/len(pbf), "busy_util": None,
        "dep_rate": sum(pdep)/len(pdep) / (a.horizon - 0.25*a.horizon),
        "lam_eff": None, "p_loss": 0.0, "p_wait": None,
        "per_seed_L": pL, "per_seed_W": pW,
        "per_seed_busy_frac": pbf, "per_seed_p_loss": [0.0]*len(seeds),
        "per_seed_p_wait": [None]*len(seeds)
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
