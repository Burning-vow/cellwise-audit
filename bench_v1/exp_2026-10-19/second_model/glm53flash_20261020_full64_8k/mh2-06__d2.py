import argparse, json, math, random, heapq
from collections import deque

def sample_serv(rng, p, r1, r2):
    return rng.expovariate(r1) if rng.random() < p else rng.expovariate(r2)

def run_seed(seed, H, lam, c, p, r1, r2):
    rng = random.Random(seed)
    w0 = 0.25 * H
    inf = float('inf')
    t = 0.0
    busy = []
    queue = deque()
    next_arr = rng.expovariate(lam)
    L_area = 0.0
    occ_area = 0.0
    busy_area = 0.0
    arr_cnt = dep_cnt = blk_cnt = 0
    sys_sum = 0.0
    waited = 0
    while True:
        ta = next_arr
        td = busy[0] if busy else inf
        tn = min(ta, td, H)
        a0, a1 = max(t, w0), min(tn, H)
        if a1 > a0:
            n = len(queue) + len(busy)
            dt = a1 - a0
            L_area += n * dt
            busy_area += len(busy) * dt
            occ_area += (1.0 if n > 0 else 0.0) * dt
        t = tn
        if t >= H:
            break
        if ta <= td:
            s = sample_serv(rng, p, r1, r2)
            if t >= w0:
                arr_cnt += 1
            if len(busy) < c:
                heapq.heappush(busy, t + s)
            else:
                queue.append((t, s))
            next_arr = t + rng.expovariate(lam)
        else:
            heapq.heappop(busy)
            if queue:
                a, s = queue.popleft()
                heapq.heappush(busy, t + s)
                if a >= w0:
                    dep_cnt += 1
                    sys_sum += t - a
                    if t - a - s > 1e-12:
                        waited += 1
    win = H - w0
    return {
        'L': L_area / win,
        'W': (sys_sum / arr_cnt) * 60.0 if arr_cnt else 0.0,
        'busy_frac': min(1.0, busy_area / win) if c == 1 else occ_area / win,
        'busy_util': busy_area / (win * c),
        'busy_occupied': occ_area / win,
        'p_loss': 0.0,
        'p_wait': waited / arr_cnt if arr_cnt else 0.0,
        'arr': arr_cnt,
        'dep': dep_cnt,
        'blk': blk_cnt,
        'dep_rate': dep_cnt / win,
        'lam_eff': arr_cnt / win,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=200.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    args = ap.parse_args()
    lam = 5.0
    c = 1
    p = 0.9
    r1 = 0.5 * 60.0
    r2 = (1.0 / 42.0) * 60.0
    if args.pert == 'lam_up':
        lam *= 1.1
    elif args.pert == 'mu_up':
        r1 *= 1.1
        r2 *= 1.1
    elif args.pert == 'c_up':
        c = 2
    seed_list = list(range(args.seed_start, args.seed_start + args.seeds))
    per = [run_seed(s, args.horizon, lam, c, p, r1, r2) for s in seed_list]
    n = len(per)
    out = {
        'L': sum(d['L'] for d in per) / n,
        'W': sum(d['W'] for d in per) / n,
        'busy_frac': sum(d['busy_frac'] for d in per) / n,
        'busy_util': sum(d['busy_util'] for d in per) / n,
        'busy_occupied': sum(d['busy_occupied'] for d in per) / n,
        'p_loss': sum(d['p_loss'] for d in per) / n,
        'p_wait': sum(d['p_wait'] for d in per) / n,
        'arr': sum(d['arr'] for d in per) / n,
        'dep': sum(d['dep'] for d in per) / n,
        'blk': sum(d['blk'] for d in per) / n,
        'dep_rate': sum(d['dep_rate'] for d in per) / n,
        'lam_eff': sum(d['lam_eff'] for d in per) / n,
        'runtime_units': 'hour',
        'time_unit': 'hour',
        'win': args.horizon * 0.75,
        'seed_list': seed_list,
        'seeds_used': n,
        'per_seed_L': [d['L'] for d in per],
        'per_seed_W': [d['W'] for d in per],
        'per_seed_busy_frac': [d['busy_frac'] for d in per],
        'per_seed_p_loss': [d['p_loss'] for d in per],
        'per_seed_p_wait': [d['p_wait'] for d in per],
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
