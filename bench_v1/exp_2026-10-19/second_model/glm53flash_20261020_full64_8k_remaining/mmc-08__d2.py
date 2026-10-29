import argparse, heapq, json, math, random

def run_seed(seed, horizon, lam, mu, c):
    rng = random.Random(seed)
    t = 0.0
    n = 0
    ev = []
    heapq.heappush(ev, (rng.expovariate(lam), 'arr', 0))
    cid = 0
    svc = {}
    start = {}
    arrive = {}
    dep_t = {}
    queue = []
    tlast = 0.0
    warm = 0.25 * horizon
    area_L = 0.0
    area_b = 0.0
    arr_c = 0
    dep_c = 0
    wait_c = 0
    soj_sum = 0.0
    while True:
        if not ev:
            break
        t, typ, i = heapq.heappop(ev)
        if t > horizon:
            break
        dt = t - tlast
        if dt > 0 and tlast >= warm:
            area_L += n * dt
            area_b += min(n, c) * dt
        elif t > warm and tlast < warm:
            area_L += n * (t - warm)
            area_b += min(n, c) * (t - warm)
        tlast = t
        if typ == 'arr':
            n += 1
            if t >= warm:
                arr_c += 1
                if n > c:
                    wait_c += 1
            svc[i] = rng.expovariate(mu)
            arrive[i] = t
            if n <= c:
                heapq.heappush(ev, (t + svc[i], 'dep', i))
            else:
                queue.append(i)
            cid += 1
            heapq.heappush(ev, (t + rng.expovariate(lam), 'arr', cid))
        else:
            n -= 1
            if t >= warm:
                dep_c += 1
                soj_sum += t - arrive[i]
            if queue:
                j = queue.pop(0)
                start[j] = t
                heapq.heappush(ev, (t + svc[j], 'dep', j))
    win = horizon - warm
    L = area_L / win
    bf = area_b / (c * win)
    W = (soj_sum / dep_c) * 60.0 if dep_c > 0 else 0.0
    pw = wait_c / arr_c if arr_c > 0 else 0.0
    return L, W, bf, pw, arr_c, dep_c

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam, mu, c = 8.0, 6.0, 3.0
    if a.pert == 'lam_up':
        lam *= 1.1
    elif a.pert == 'mu_up':
        mu *= 1.1
    elif a.pert == 'c_up':
        c += 1
    perL, perW, perBF, perPW, perPL = [], [], [], [], []
    seed_list = []
    sa = sd = 0.0
    for k in range(a.seeds):
        s = a.seed_start + k
        L, W, bf, pw, ac, dc = run_seed(s, a.horizon, lam, mu, c)
        seed_list.append(s)
        perL.append(L); perW.append(W); perBF.append(bf)
        perPW.append(pw); perPL.append(0.0)
        sa += ac; sd += dc
    ns = a.seeds
    win = a.horizon - 0.25 * a.horizon
    out = {
        'L': sum(perL) / ns,
        'W': sum(perW) / ns,
        'busy_frac': sum(perBF) / ns,
        'p_wait': sum(perPW) / ns,
        'runtime_units': 1,
        'seed_list': seed_list,
        'seeds_used': ns,
        'time_unit': 'hour',
        'win': win,
        'arr': sa / ns,
        'blk': 0.0,
        'busy_util': sum(perBF) / ns,
        'busy_occupied': 1.0 - math.exp(-0.0) if False else None,
        'dep': sd / ns,
        'dep_rate': sd / (ns * win),
        'lam_eff': sa / (ns * win),
        'p_loss': 0.0,
        'per_seed_L': perL,
        'per_seed_W': perW,
        'per_seed_busy_frac': perBF,
        'per_seed_p_loss': perPL,
        'per_seed_p_wait': perPW,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
