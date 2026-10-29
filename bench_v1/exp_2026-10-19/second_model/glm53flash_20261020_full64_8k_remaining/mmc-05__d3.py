import argparse, json, math, random, heapq

def run_seed(seed, H, lam, mu, c):
    rng = random.Random(seed)
    T_warm = 0.25 * H
    t = 0.0
    n = 0
    queue = []
    busy = []  # heap of departure times
    area_n = 0.0
    area_busy = 0.0
    area_occ = 0.0
    t_last = 0.0
    wait_sum = 0.0
    dep_cnt = 0
    arr_cnt = 0
    q_cnt = 0
    arr_cnt_w = 0
    q_cnt_w = 0
    eventq = []
    heapq.heappush(eventq, (rng.expovariate(lam), 'arr'))
    last_arr = None
    while True:
        if not eventq:
            break
        te, kind = heapq.heappop(eventq)
        if te > H:
            break
        if t_last > T_warm:
            dt = te - t_last
            area_n += n * dt
            b = min(n, c)
            area_busy += b * dt
            if n > 0:
                area_occ += dt
        t_last = te
        if kind == 'arr':
            n += 1
            svc = rng.expovariate(mu)
            nxt = te + rng.expovariate(lam)
            if nxt <= H:
                heapq.heappush(eventq, (nxt, 'arr'))
            if te >= T_warm:
                arr_cnt += 1
            if len(busy) < c:
                dep_t = te + svc
                heapq.heappush(busy, dep_t)
                heapq.heappush(eventq, (dep_t, 'dep'))
                waited = 0.0
            else:
                queue.append((te, svc))
                waited = None
            if te >= T_warm:
                arr_cnt_w += 1
                if waited is None:
                    q_cnt_w += 1
                else:
                    q_cnt += 0
            if waited is not None and te >= T_warm:
                pass
            arrival_info.append((te, waited))
        else:
            n -= 1
            heapq.heappop(busy) if False else None
            if queue:
                a_t, svc = queue.pop(0)
                dep_t = te + svc
                heapq.heappush(busy, dep_t)
                heapq.heappush(eventq, (dep_t, 'dep'))
                waited = te - a_t
            else:
                waited = 0.0
            if te >= T_warm:
                dep_cnt += 1
            departure_info.append((te, a_t_lookup))
        break
    return {}

arrival_info = []
departure_info = []
a_map = {}

def simulate(seed, H, lam, mu, c):
    global arrival_info, departure_info, a_map
    arrival_info = []
    departure_info = []
    a_map = {}
    rng = random.Random(seed)
    T_warm = 0.25 * H
    n = 0
    queue = []
    busy = []
    ev = []
    heapq.heappush(ev, (rng.expovariate(lam), 0, 'arr'))
    t_last = 0.0
    area_n = area_busy = area_occ = 0.0
    wait_sum = 0.0
    dep_cnt = arr_cnt = q_cnt = 0
    aid = 0
    while ev:
        te, _, kind = heapq.heappop(ev)
        if te > H:
            break
        if t_last > T_warm:
            dt = te - t_last
            area_n += n * dt
            area_busy += min(n, c) * dt
            if n > 0:
                area_occ += dt
        t_last = te
        if kind == 'arr':
            svc = rng.expovariate(mu)
            a_map[aid] = (te, None)
            aid += 1
            nt = te + rng.expovariate(lam)
            if nt <= H:
                heapq.heappush(ev, (nt, 0, 'arr'))
            n += 1
            if len(busy) < c:
                dt2 = te + svc
                heapq.heappush(busy, dt2)
                heapq.heappush(ev, (dt2, 0, 'dep'))
                a_map[aid - 1] = (te, te)
            else:
                queue.append((te, svc))
                if te >= T_warm:
                    q_cnt += 1
            if te >= T_warm:
                arr_cnt += 1
        else:
            n -= 1
            if busy:
                heapq.heappop(busy)
            if queue:
                a_t, svc = queue.pop(0)
                dt2 = te + svc
                heapq.heappush(busy, dt2)
                heapq.heappush(ev, (dt2, 0, 'dep'))
            if te >= T_warm:
                dep_cnt += 1
    win = H - T_warm
    if win <= 0:
        win = max(H, 1e-9)
    L = area_n / win
    busy_frac = area_busy / (c * win)
    busy_util = busy_frac
    occupied = area_occ / win
    dep_rate = dep_cnt / win
    p_wait = q_cnt / arr_cnt if arr_cnt > 0 else 0.0
    return dict(L=L, busy_frac=busy_frac, busy_util=busy_util, busy_occupied=occupied,
                p_wait=p_wait, arr=arr_cnt, dep=dep_cnt, blk=0, p_loss=0.0,
                dep_rate=dep_rate, lam_eff=arr_cnt / win, win=win)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=10)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu, c = 10.0, 10.0, 2
    if a.pert == 'lam_up':
        lam *= 1.1
    elif a.pert == 'mu_up':
        mu *= 1.1
    elif a.pert == 'c_up':
        c += 1
    seeds = list(range(a.seed_start, a.seed_start + a.seeds))
    res = [simulate(s, a.horizon, lam, mu, c) for s in seeds]
    k = len(res)
    def avg(f):
        return sum(r[f] for r in res) / k if k else 0.0
    out = {
        'L': avg('L'),
        'W': avg('L') / (avg('dep_rate') / 60.0) if avg('dep_rate') > 0 else 0.0,
        'busy_frac': avg('busy_frac'),
        'busy_util': avg('busy_util'),
        'busy_occupied': avg('busy_occupied'),
        'p_wait': avg('p_wait'),
        'p_loss': avg('p_loss'),
        'arr': avg('arr'),
        'dep': avg('dep'),
        'blk': avg('blk'),
        'dep_rate': avg('dep_rate'),
        'lam_eff': avg('lam_eff'),
        'runtime_units': 'hours',
        'seed_list': seeds,
        'seeds_used': k,
        'time_unit': 'hour',
        'win': res[0]['win'] if res else 0.0,
        'per_seed_L': [r['L'] for r in res],
        'per_seed_W': [r['L'] / (r['dep_rate'] / 60.0) if r['dep_rate'] > 0 else 0.0 for r in res],
        'per_seed_busy_frac': [r['busy_frac'] for r in res],
        'per_seed_p_loss': [r['p_loss'] for r in res],
        'per_seed_p_wait': [r['p_wait'] for r in res],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
