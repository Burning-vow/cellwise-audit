import argparse, json, heapq, random, math

def run(seed, horizon, lam, mu):
    rng = random.Random(seed)
    t = 0.0
    t_end = horizon
    warm = 0.25 * horizon
    queue = []
    events = []
    heapq.heappush(events, (rng.expovariate(lam), "arr"))
    n = 0
    busy = False
    area_N = 0.0
    area_B = 0.0
    in_win_time = 0.0
    last = 0.0
    st_count = 0
    st_wait = 0.0
    wt_wait = 0.0
    wt_count = 0
    dep_cnt = 0
    arr_cnt = 0
    loss_cnt = 0
    def integral(a, b, Nv, Bv):
        nonlocal area_N, area_B, in_win_time
        lo = max(a, warm)
        if b > lo:
            area_N += Nv * (b - lo)
            area_B += Bv * (b - lo)
            in_win_time += b - lo
    while t < t_end:
        t, typ = heapq.heappop(events)
        if t > t_end:
            break
        integral(last, t, n, 1.0 if busy else 0.0)
        last = t
        if typ == "arr":
            arr_cnt += 1
            if t >= warm:
                st_count += 1
            svc = rng.expovariate(mu)
            if n == 0:
                wt = 0.0
                busy = True
                heapq.heappush(events, (t + svc, "dep"))
            else:
                queue.append((t, svc))
            n += 1
            heapq.heappush(events, (t + rng.expovariate(lam), "arr"))
        else:
            dep_cnt += 1
            n -= 1
            if n == 0:
                busy = False
            else:
                a0, svc = queue.pop(0)
                heapq.heappush(events, (t + svc, "dep"))
        if queue:
            pass
    return {"L": area_N / in_win_time if in_win_time > 0 else 0.0,
            "busy_frac": area_B / in_win_time if in_win_time > 0 else 0.0,
            "arr": arr_cnt / (horizon - warm) if horizon > warm else 0.0,
            "dep": dep_cnt / (horizon - warm) if horizon > warm else 0.0,
            "W": None, "_n": st_count, "_dep2": dep_cnt}

def run2(seed, horizon, lam, mu):
    rng = random.Random(seed)
    t_end = horizon
    warm = 0.25 * horizon
    events = []
    heapq.heappush(events, (rng.expovariate(lam), "arr", None))
    n = 0
    busy = False
    area_N = 0.0
    area_B = 0.0
    win_time = 0.0
    last = 0.0
    waits = []
    dep_cnt = 0
    arr_cnt = 0
    while events:
        t, typ, info = heapq.heappop(events)
        if t > t_end:
            break
        lo = max(last, warm)
        if t > lo:
            dt = t - lo
            area_N += n * dt
            area_B += (1.0 if busy else 0.0) * dt
            win_time += dt
        last = t
        if typ == "arr":
            arr_cnt += 1
            svc = rng.expovariate(mu)
            if n == 0:
                busy = True
                heapq.heappush(events, (t + svc, "dep", (t, svc)))
            else:
                pass
            n += 1
            heapq.heappush(events, (t + rng.expovariate(lam), "arr", None))
            if typ == "arr" and n > 1:
                waits.append((t, svc))
            else:
                waits.append((t, svc))
        else:
            dep_cnt += 1
            if t >= warm:
                a0, svc = info
                waits_done = (t - a0)
                waits[-1] = waits_done
            n -= 1
            if n == 0:
                busy = False
            else:
                a0, svc = waits_pend.pop(0)
                heapq.heappush(events, (t + svc, "dep", (a0, svc)))
    return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=10000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    lam, mu, c = 4.0, 12.0, 1.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    time_unit = "minute"
    lam_m = lam / 60.0
    mu_m = 1.0 / 5.0 if mu == 12.0 else mu / 60.0
    mu_m = 0.2
    horizon = a.horizon
    warm = 0.25 * horizon
    per_L, per_W, per_B, per_pw, per_pl = [], [], [], [], []
    seed_list = []
    tot_arr = tot_dep = 0.0
    for k in range(a.seeds):
        seed = a.seed_start + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t_end = horizon
        events = []
        heapq.heappush(events, (rng.expovariate(lam_m), "arr", None))
        n = 0
        busy = False
        area_N = area_B = win_time = 0.0
        last = 0.0
        pend = []
        waits = []
        arr_c = dep_c = 0
        while events:
            t, typ, info = heapq.heappop(events)
            if t > t_end:
                break
            lo = max(last, warm)
            if t > lo:
                dt = t - lo
                area_N += n * dt
                area_B += (1.0 if busy else 0.0) * dt
                win_time += dt
            last = t
            if typ == "arr":
                arr_c += 1
                svc = rng.expovariate(mu_m)
                if n == 0:
                    busy = True
                    heapq.heappush(events, (t + svc, "dep", (t, svc)))
                else:
                    pend.append((t, svc))
                n += 1
                heapq.heappush(events, (t + rng.expovariate(lam_m), "arr", None))
            else:
                dep_c += 1
                a0, svc = info
                if a0 >= warm:
                    waits.append(t - a0)
                n -= 1
                if n == 0:
                    busy = False
                else:
                    a0b, svcb = pend.pop(0)
                    heapq.heappush(events, (t + svcb, "dep", (a0b, svcb)))
        win = horizon - warm
        per_L.append(area_N / win_time if win_time > 0 else 0.0)
        per_B.append(area_B / win_time if win_time > 0 else 0.0)
        per_W.append(sum(waits) / len(waits) if waits else 0.0)
        per_pw.append(sum(1 for w in waits if w > 0) / len(waits) if waits else 0.0)
        per_pl.append(0.0)
        tot_arr += arr_c / win
        tot_dep += dep_c / win
    S = a.seeds
    out = {
        "L": sum(per_L) / S, "W": sum(per_W) / S,
        "busy_frac": sum(per_B) / S, "p_wait": sum(per_pw) / S,
        "runtime_units": time_unit, "seed_list": seed_list,
        "seeds_used": S, "time_unit": time_unit, "win": horizon - warm,
        "arr": tot_arr / S, "blk": 0.0, "busy_util": sum(per_B) / S,
        "busy_occupied": sum(per_B) / S, "dep": tot_dep / S,
        "dep_rate": tot_dep / S, "lam_eff": tot_arr / S, "p_loss": 0.0,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_B, "per_seed_p_loss": per_pl,
        "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
