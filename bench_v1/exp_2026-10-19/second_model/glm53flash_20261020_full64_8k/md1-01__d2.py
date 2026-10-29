import argparse, json, random, math, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=10)
    ap.add_argument("--horizon", type=float, default=400000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    unit = "minute"
    lam = 4.0/60.0
    mu_rate = 1.0/6.0
    c = 1.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu_rate *= 1.1
    elif a.pert == "c_up": c = 2.0
    srv = 1.0/mu_rate
    warm = 0.25*H
    win = H - warm
    per_L=[]; per_W=[]; per_bf=[]; per_pl=[]; per_pw=[]
    seed_list=[]; arr_tot=0.0; dep_tot=0.0; blk_tot=0.0
    for k in range(n_seeds):
        seed = S+k
        seed_list.append(seed)
        rng = random.Random(seed*2654435761 % (2**31) + 12345)
        t = 0.0; q = []; busy_until = -1.0
        servers = int(c)
        in_serv = []  # end times
        area_N = 0.0; area_busy = 0.0
        n = 0
        arr = 0; dep = 0; blk = 0
        wait_sum = 0.0; stay_sum = 0.0; stay_cnt = 0
        waited = 0; served = 0
        last = 0.0
        def advance(nt):
            nonlocal area_N, area_busy, last, n
            dt = nt - last
            if dt > 0:
                if last >= warm:
                    area_N += n*dt
                    area_busy += min(n, servers)*dt
                elif nt > warm:
                    f = (nt - warm)/dt
                    area_N += n*dt*f
                    area_busy += min(n, servers)*dt*f
            last = nt
        while t < H:
            nt_arr = t + rng.expovariate(lam)
            if in_serv:
                nt_dep = min(in_serv)
            else:
                nt_dep = math.inf
            if nt_arr <= nt_dep and nt_arr <= H:
                advance(nt_arr); t = nt_arr
                arr += 1
                svc = srv
                if len(in_serv) < servers:
                    in_serv.append(t + svc)
                    waited += 0
                    st = t
                    stay_sum += svc; stay_cnt += 1; served += 1
                    dep += 0
                else:
                    q.append((t, svc))
                    waited += 1
                n += 1
            elif nt_dep <= H:
                advance(nt_dep); t = nt_dep
                in_serv.remove(nt_dep)
                dep += 1
                n -= 1
                if q:
                    at, svc = q.pop(0)
                    st_start = t
                    in_serv.append(t + svc)
                    stay_sum += (t - at) + svc; stay_cnt += 1
            else:
                advance(H); t = H
        # drain not needed; departures already counted when they occur within H
        # count blocked/lost: none in this model (infinite queue), unless queue cap
        per_L.append(area_N/win)
        per_W.append(stay_sum/stay_cnt if stay_cnt else 0.0)
        per_bf.append(area_busy/win/c)
        per_pl.append(0.0)
        per_pw.append(waited/arr if arr else 0.0)
        arr_tot += arr; dep_tot += dep; blk_tot += blk
    m = n_seeds
    L = sum(per_L)/m
    W = sum(per_W)/m
    bf = sum(per_bf)/m
    p_wait = sum(per_pw)/m
    p_loss = 0.0
    out = {
        "L": L, "W": W, "busy_frac": bf,
        "runtime_units": unit, "seed_list": seed_list,
        "seeds_used": m, "time_unit": unit, "win": win,
        "arr": arr_tot/m, "dep": dep_tot/m, "blk": blk_tot/m,
        "dep_rate": dep_tot/m/win, "lam_eff": (arr_tot-blk_tot)/m/win,
        "p_loss": p_loss, "p_wait": p_wait,
        "busy_util": bf, "busy_occupied": bf,
        "per_seed_L": per_L, "per_seed_W": per_W,
        "per_seed_busy_frac": per_bf,
        "per_seed_p_loss": per_pl, "per_seed_p_wait": per_pw,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
