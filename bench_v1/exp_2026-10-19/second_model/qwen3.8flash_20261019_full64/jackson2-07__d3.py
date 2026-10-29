import random, json, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=1)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    lam = 6.0; mu = 10.0
    if a.pert == 'lam_up': lam *= 1.2
    elif a.pert == 'mu_up': mu *= 1.2
    elif a.pert == 'c_up': pass
    H = a.horizon; warm = 0.25 * H; win = H - warm
    seeds_used = a.seeds; seed_list = [a.seed_start + i for i in range(seeds_used)]
    tot_L = 0.0; tot_W = 0.0; tot_arr = 0; tot_dep = 0; tot_blk = 0
    tot_busy_frac = 0.0; tot_p_loss = 0.0; tot_p_wait = 0.0
    per_seed_L = []; per_seed_W = []; per_seed_busy_frac = []
    per_seed_p_loss = []; per_seed_p_wait = []
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0; next_arr = rng.expovariate(lam)
        q1 = []; q2 = []; srv1_end = None; srv2_end = None
        custs = {}
        area_L = 0.0; last_t = 0.0; sum_W = 0.0; n_dep = 0; n_arr = 0; n_blk = 0
        busy1_time = 0.0; busy2_time = 0.0; wait_count = 0
        events = []
        def add_event(time, typ, data=None):
            events.append((time, typ, data))
        add_event(next_arr, 'arr')
        while events:
            events.sort(key=lambda x: (x[0], {'dep2':0,'srv1_done':1,'srv2_done':2,'arr':3}))
            et, typ, data = events.pop(0)
            if et > H: break
            dt = et - last_t
            if last_t >= warm:
                L_now = len(q1) + len(q2) + (1 if srv1_end is not None else 0) + (1 if srv2_end is not None else 0)
                area_L += L_now * dt
            last_t = et
            if typ == 'arr':
                n_arr += 1
                dur1 = rng.expovariate(mu); dur2 = rng.expovariate(mu)
                cid = f"c{n_arr}"
                custs[cid] = {'dur1': dur1, 'dur2': dur2, 't0': et}
                if srv1_end is None and not q1:
                    srv1_end = et + dur1
                    add_event(srv1_end, 'srv1_done', cid)
                else:
                    q1.append(cid)
                add_event(et + rng.expovariate(lam), 'arr')
            elif typ == 'srv1_done':
                cid = data
                c = custs[cid]
                srv1_end = None
                if q1:
                    nc = q1.pop(0)
                    srv1_end = et + custs[nc]['dur1']
                    add_event(srv1_end, 'srv1_done', nc)
                if srv2_end is None and not q2:
                    srv2_end = et + c['dur2']
                    add_event(srv2_end, 'srv2_done', cid)
                else:
                    q2.append(cid)
            elif typ == 'srv2_done':
                cid = data
                c = custs[cid]
                srv2_end = None
                if q2:
                    nc = q2.pop(0)
                    srv2_end = et + custs[nc]['dur2']
                    add_event(srv2_end, 'srv2_done', nc)
                w = et - c['t0']
                if et >= warm:
                    sum_W += w; n_dep += 1
                del custs[cid]
        if last_t < H:
            dt = H - last_t
            if last_t >= warm:
                L_now = len(q1) + len(q2) + (1 if srv1_end is not None else 0) + (1 if srv2_end is not None else 0)
                area_L += L_now * dt
        L_est = area_L / win if win > 0 else 0.0
        W_est = sum_W / n_dep if n_dep > 0 else 0.0
        bf = ((busy1_time + busy2_time) / (2 * H)) if H > 0 else 0.0
        pl = n_blk / n_arr if n_arr > 0 else 0.0
        pw = wait_count / n_arr if n_arr > 0 else 0.0
        per_seed_L.append(L_est); per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf); per_seed_p_loss.append(pl); per_seed_p_wait.append(pw)
        tot_L += L_est; tot_W += W_est; tot_arr += n_arr; tot_dep += n_dep; tot_blk += n_blk
        tot_busy_frac += bf; tot_p_loss += pl; tot_p_wait += pw
    avg_L = tot_L / seeds_used; avg_W = tot_W / seeds_used
    avg_arr = tot_arr / seeds_used; avg_dep = tot_dep / seeds_used; avg_blk = tot_blk / seeds_used
    avg_bf = tot_busy_frac / seeds_used; avg_pl = tot_p_loss / seeds_used; avg_pw = tot_p_wait / seeds_used
    dep_rate = avg_dep / win if win > 0 else 0.0
    out = {
        "L": round(avg_L, 4), "W": round(avg_W, 4), "runtime_units": "minute",
        "seed_list": seed_list, "seeds_used": seeds_used, "time_unit": "hour",
        "win": round(win, 4), "arr": round(avg_arr, 4), "blk": round(avg_blk, 4),
        "busy_frac": round(avg_bf, 4), "busy_util": round(avg_bf, 4),
        "dep": round(avg_dep, 4), "dep_rate": round(dep_rate, 4),
        "lam_eff": round(avg_arr / win, 4) if win > 0 else 0.0,
        "p_loss": round(avg_pl, 4), "p_wait": round(avg_pw, 4),
        "per_seed_L": [round(x, 4) for x in per_seed_L],
        "per_seed_W": [round(x, 4) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 4) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 4) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 4) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
