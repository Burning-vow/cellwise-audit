import argparse, json, math, random, sys

def sim_run(seed, H, lam, m, p1, r1, r2):
    rng = random.Random(seed)
    T0 = 0.25 * H
    t = 0.0
    n = 0
    next_arr = rng.expovariate(lam)
    next_dep = float('inf')
    area = 0.0
    busy_area = 0.0
    wait_sum = 0.0
    soj_sum = 0.0
    arr_n = 0
    dep_n = 0
    loss_n = 0
    waited_n = 0
    done_n = 0
    last = 0.0
    while t < H:
        t_next = min(next_arr, next_dep)
        if t_next >= H:
            t_next = H
        if t_next > T0:
            area += n * (t_next - max(t, T0))
            busy_area += (1 if n >= 1 else 0) * (t_next - max(t, T0))
        t = t_next
        if t >= H:
            break
        if next_arr <= next_dep:
            n += 1
            if t >= T0:
                arr_n += 1
            svc = 1.0 / r1 if rng.random() < p1 else 1.0 / r2
            if n == 1:
                next_dep = t + svc
                if t >= T0:
                    waited_n += 0
            else:
                if t >= T0:
                    waited_n += 1
                wait_sum += 0.0
            if n >= 2:
                pass
            next_arr = t + rng.expovariate(lam)
        else:
            n -= 1
            if t >= T0:
                dep_n += 1
            next_dep = float('inf')
            if n >= 1:
                pass
            next_dep_pending = True
            if n >= 1:
                next_dep = t + (1.0 / r1 if rng.random() < p1 else 1.0 / r2)
        last = t
    arr_n = 0
    dep_n = 0
    return None

def run_seed(seed, H, lam, m, p1, r1, r2):
    rng = random.Random(seed)
    T0 = 0.25 * H
    t = 0.0
    n = 0
    next_arr = rng.expovariate(lam)
    next_dep = float('inf')
    area = 0.0
    busy_area = 0.0
    soj_sum = 0.0
    arr_n = 0
    dep_n = 0
    waited_n = 0
    queue = []
    while t < H:
        t_next = min(next_arr, next_dep, H)
        if t_next > T0:
            dt = t_next - max(t, T0)
            area += n * dt
            busy_area += (1 if n >= 1 else 0) * dt
        t = t_next
        if t >= H:
            break
        if next_arr <= next_dep:
            svc = 1.0 / r1 if rng.random() < p1 else 1.0 / r2
            arr_time = t
            n += 1
            if t >= T0:
                arr_n += 1
            if n == 1:
                next_dep = t + svc
                dep_t = t + svc
            else:
                waited_n += 1
                dep_t = None
            queue.append((arr_time, svc, t >= T0))
            next_arr = t + rng.expovariate(lam)
        else:
            n -= 1
            item = None
            for k, q in enumerate(queue):
                if not q[2]:
                    continue
                item = q
                queue.pop(k)
                break
            if item is None and queue:
                item = queue.pop(0)
            if t >= T0:
                dep_n += 1
                if item is not None:
                    soj_sum += t - item[0]
            if n >= 1:
                nxt = queue[0]
                if not nxt[1]:
                    pass
                next_dep = t + nxt[1]
            else:
                next_dep = float('inf')
    win = H - T0
    L = area / win
    busy = busy_area / win
    W = (soj_sum / dep_n) * 60.0 if dep_n > 0 else 0.0
    p_wait = waited_n / arr_n if arr_n > 0 else 0.0
    return L, W, busy, p_wait, arr_n, dep_n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=float, default=10)
    ap.add_argument('--horizon', type=float, default=10000)
    ap.add_argument('--seed-start', type=float, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    N = int(a.seeds)
    H = float(a.horizon)
    S = int(a.seed_start)
    lam = 3.0
    m = 0.1
    if a.pert == 'lam_up':
        lam = lam * 1.1
    elif a.pert == 'mu_up':
        m = m / 1.1
    elif a.pert == 'c_up':
        m = m * 1.1
    cv2 = 9.0
    p1 = (1.0 + math.sqrt(0.8)) / 2.0
    p2 = 1.0 - p1
    r1 = 2.0 * p1 / m
    r2 = 2.0 * p2 / m
    Ls, Ws, Bs, Ps, As, Ds = [], [], [], [], [], []
    seeds_used = 0
    seed_list = []
    for i in range(N):
        s = S + i
        L, W, busy, p_wait, an, dn = run_seed(s, H, lam, m, p1, r1, r2)
        seed_list.append(s)
        Ls.append(L); Ws.append(W); Bs.append(busy); Ps.append(p_wait)
        As.append(an); Ds.append(dn)
        seeds_used += 1
    n = seeds_used
    out = {
        'L': sum(Ls) / n,
        'W': sum(Ws) / n,
        'busy_frac': sum(Bs) / n,
        'busy_util': sum(Bs) / n,
        'busy_occupied': sum(Bs) / n,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'hour',
        'win': 0.75 * H,
        'arr': sum(As) / n,
        'blk': 0.0,
        'dep': sum(Ds) / n,
        'dep_rate': (sum(Ds) / n) / (0.75 * H),
        'lam_eff': (sum(Ds) / n) / (0.75 * H),
        'p_loss': 0.0,
        'p_wait': sum(Ps) / n,
        'per_seed_L': Ls,
        'per_seed_W': Ws,
        'per_seed_busy_frac': Bs,
        'per_seed_p_loss': [0.0] * n,
        'per_seed_p_wait': Ps,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
