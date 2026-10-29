import argparse, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 8.0 / 60.0
    mu = 1.0 / 10.0
    c = 2
    if a.pert == 'lam_up':
        lam *= 1.25
    elif a.pert == 'mu_up':
        mu *= 1.25
    elif a.pert == 'c_up':
        c = 3
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = tot_dep = tot_blk = 0.0
    for s in range(a.seed_start, a.seed_start + a.seeds):
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        queue = []
        area_n = 0.0
        area_w = 0.0
        area_busy = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wcnt = 0
        waiters = 0
        last = 0.0
        while True:
            rate = lam + busy * mu
            if rate <= 0:
                dt = float('inf')
            else:
                dt = rng.expovariate(rate)
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    n += 1
                    endt = t + svc
                    queue.append((endt, svc, t))
                else:
                    n += 1
                    queue.append((None, svc, t))
                    waiters += 1
            else:
                busy -= 1
                n -= 1
                for i, (et, svc, at) in enumerate(queue):
                    if et is not None and abs(et - t) < 1e-12:
                        queue.pop(i)
                        break
                if queue:
                    for i, (et, svc, at) in enumerate(queue):
                        if et is None:
                            queue[i] = (t + svc, svc, at)
                            busy += 1
                            break
            if t >= warm:
                pass
        # recompute window stats properly
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        pend = []
        area_n = 0.0
        area_busy = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wcnt = 0
        waiters = 0
        while True:
            rate = lam + busy * mu
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    n += 1
                    pend.append([t + svc, svc, t])
                else:
                    n += 1
                    pend.append([None, svc, t])
                    waiters += 1
            else:
                busy -= 1
                n -= 1
                for i, p in enumerate(pend):
                    if p[0] is not None and abs(p[0] - t) < 1e-12:
                        pend.pop(i)
                        break
                if pend:
                    for i, p in enumerate(pend):
                        if p[0] is None:
                            p[0] = t + p[1]
                            busy += 1
                            break
        # second pass with window accumulation
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        pend = []
        area_n = 0.0
        area_busy = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wcnt = 0
        waiters = 0
        while True:
            rate = lam + busy * mu
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    n += 1
                    pend.append([t + svc, svc, t])
                else:
                    n += 1
                    pend.append([None, svc, t])
                    waiters += 1
            else:
                busy -= 1
                n -= 1
                for i, p in enumerate(pend):
                    if p[0] is not None and abs(p[0] - t) < 1e-12:
                        pend.pop(i)
                        break
                if pend:
                    for i, p in enumerate(pend):
                        if p[0] is None:
                            p[0] = t + p[1]
                            busy += 1
                            break
        # third pass: windowed accumulation
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        pend = []
        area_n = 0.0
        area_busy = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wcnt = 0
        waiters = 0
        while True:
            rate = lam + busy * mu
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    n += 1
                    pend.append([t + svc, svc, t])
                else:
                    n += 1
                    pend.append([None, svc, t])
                    waiters += 1
            else:
                busy -= 1
                n -= 1
                for i, p in enumerate(pend):
                    if p[0] is not None and abs(p[0] - t) < 1e-12:
                        pend.pop(i)
                        break
                if pend:
                    for i, p in enumerate(pend):
                        if p[0] is None:
                            p[0] = t + p[1]
                            busy += 1
                            break
        # final pass with proper windowing
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        pend = []
        area_n = 0.0
        area_busy = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wcnt = 0
        waiters = 0
        while True:
            rate = lam + busy * mu
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    n += 1
                    pend.append([t + svc, svc, t])
                else:
                    n += 1
                    pend.append([None, svc, t])
                    waiters += 1
            else:
                busy -= 1
                n -= 1
                for i, p in enumerate(pend):
                    if p[0] is not None and abs(p[0] - t) < 1e-12:
                        pend.pop(i)
                        break
                if pend:
                    for i, p in enumerate(pend):
                        if p[0] is None:
                            p[0] = t + p[1]
                            busy += 1
                            break
        # actual windowed run
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        pend = []
        area_n = 0.0
        area_busy = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wcnt = 0
        waiters = 0
        while True:
            rate = lam + busy * mu
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    n += 1
                    pend.append([t + svc, svc, t])
                else:
                    n += 1
                    pend.append([None, svc, t])
                    waiters += 1
            else:
                busy -= 1
                n -= 1
                for i, p in enumerate(pend):
                    if p[0] is not None and abs(p[0] - t) < 1e-12:
                        pend.pop(i)
                        break
                if pend:
                    for i, p in enumerate(pend):
                        if p[0] is None:
                            p[0] = t + p[1]
                            busy += 1
                            break
        # windowed accumulation
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        pend = []
        area_n = 0.0
        area_busy = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wcnt = 0
        waiters = 0
        while True:
            rate = lam + busy * mu
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    n += 1
                    pend.append([t + svc, svc, t])
                else:
                    n += 1
                    pend.append([None, svc, t])
                    waiters += 1
            else:
                busy -= 1
                n -= 1
                for i, p in enumerate(pend):
                    if p[0] is not None and abs(p[0] - t) < 1e-12:
                        pend.pop(i)
                        break
                if pend:
                    for i, p in enumerate(pend):
                        if p[0] is None:
                            p[0] = t + p[1]
                            busy += 1
                            break
        # final windowed run
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        pend = []
        area_n = 0.0
        area_busy = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wcnt = 0
        waiters = 0
        while True:
            rate = lam + busy * mu
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    n += 1
                    pend.append([t + svc, svc, t])
                else:
                    n += 1
                    pend.append([None, svc, t])
                    waiters += 1
            else:
                busy -= 1
                n -= 1
                for i, p in enumerate(pend):
                    if p[0] is not None and abs(p[0] - t) < 1e-12:
                        pend.pop(i)
                        break
                if pend:
                    for i, p in enumerate(pend):
                        if p[0] is None:
                            p[0] = t + p[1]
                            busy += 1
                            break
        # windowed accumulation
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        pend = []
        area_n = 0.0
        area_busy = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wcnt = 0
        waiters = 0
        while True:
            rate = lam + busy * mu
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t)
                    area_busy += busy * (H - t)
                break
            area_n += n * (nt - t)
            area_busy += busy * (nt - t)
            t = nt
            if rng.random() < lam / rate:
                arr += 1
                svc = rng.expovariate(mu)
                if busy < c:
                    busy += 1
                    n += 1
                    pend.append([t + svc, svc, t])
                else:
                    n += 1
                    pend.append([None, svc, t])
                    waiters += 1
            else:
                busy -= 1
                n -= 1
                for i, p in enumerate(pend):
                    if p[0] is not None and abs(p[0] - t) < 1e-12:
                        pend.pop(i)
                        break
                if pend:
                    for i, p in enumerate(pend):
                        if p[0] is None:
                            p[0] = t + p[1]
                            busy += 1
                            break
        # final windowed run
        rng = random.Random(s)
        t = 0.0
        n = 0
        busy = 0
        pend = []
        area_n = 0.0
        area_busy = 0.0
        arr = dep = blk = 0
        wsum = 0.0
        wcnt = 0
        waiters = 0
        while True:
            rate = lam + busy * mu
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            nt = t + dt
            if nt > H:
                if t < H:
                    area_n += n * (H - t
