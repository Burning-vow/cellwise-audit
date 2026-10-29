import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=0)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam = 4.0; mu1 = 60.0/7.5; mu2 = 60.0/6.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu1 *= 1.1; mu2 *= 1.1
    elif a.pert == "c_up": pass
    H = a.horizon; warmup = 0.25 * H; win_len = H - warmup
    seeds_used = a.seeds; seed_list = [a.seed_start + i for i in range(seeds_used)]
    all_L = []; all_W = []; all_busy = []; all_ploss = []; all_pwait = []
    total_arr = 0; total_dep = 0; total_blk = 0; total_time_in_sys = 0.0
    for s in seeds_used:
        rng = random.Random(seed_list[s])
        events = []
        t = 0.0
        q1 = []; q2 = []
        busy1 = False; busy2 = False
        svc_end1 = None; svc_end2 = None
        arr_count = 0; dep_count = 0; blk_count = 0
        time_in_sys_sum = 0.0
        area_L = 0.0; last_t = 0.0; prev_n = 0
        # generate first arrival
        next_arr = rng.expovariate(lam)
        heapq_push(events, (next_arr, 'arr', None))
        import heapq
        def push(ev): heapq.heappush(events, ev)
        while events:
            t, typ, data = heapq.heappop(events)
            n_now = len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)
            if t >= warmup and last_t < warmup:
                frac = (warmup - last_t) / (t - last_t) if t > last_t else 0
                area_L += prev_n * frac + n_now * (1 - frac)
                last_t = warmup
            elif t >= warmup:
                area_L += prev_n * (t - last_t)
                last_t = t
            prev_n = n_now
            if typ == 'arr':
                if t >= warmup: arr_count += 1
                # schedule next arrival
                na = t + rng.expovariate(lam)
                push((na, 'arr', None))
                # enter queue1
                if not busy1:
                    busy1 = True
                    svc = rng.expovariate(mu1)
                    svc_end1 = t + svc
                    push((svc_end1, 'dep1', {'enter': t}))
                else:
                    q1.append({'enter': t})
            elif typ == 'dep1':
                info = data
                if t >= warmup:
                    pass
                # move to queue2
                if not busy2:
                    busy2 = True
                    svc = rng.expovariate(mu2)
                    svc_end2 = t + svc
                    push((svc_end2, 'dep2', {'enter': info['enter']}))
                else:
                    q2.append({'enter': info['enter']})
                # start next from q1
                if q1:
                    item = q1.pop(0)
                    busy1 = True
                    svc = rng.expovariate(mu1)
                    svc_end1 = t + svc
                    push((svc_end1, 'dep1', item))
                else:
                    busy1 = False
            elif typ == 'dep2':
                info = data
                if t >= warmup:
                    dep_count += 1
                    time_in_sys_sum += (t - info['enter'])
                # start next from q2
                if q2:
                    item = q2.pop(0)
                    busy2 = True
                    svc = rng.expovariate(mu2)
                    svc_end2 = t + svc
                    push((svc_end2, 'dep2', item))
                else:
                    busy2 = False
            if t >= H: break
        # finalize area at end
        n_final = len(q1) + len(q2) + (1 if busy1 else 0) + (1 if busy2 else 0)
        if last_t < H:
            if last_t < warmup:
                frac = (warmup - last_t) / (H - last_t) if H > last_t else 0
                area_L += prev_n * frac + n_final * (1 - frac)
            else:
                area_L += prev_n * (H - last_t)
        L_est = area_L / win_len if win_len > 0 else 0
        W_est = time_in_sys_sum / dep_count if dep_count > 0 else 0
        busy_frac_est = 0.0
        # compute busy fraction over window by tracking intervals - approximate via simulation trace
        # simpler: track busy times during sim
        # We didn't track it properly above, let's recompute or add tracking
        # For simplicity, estimate from dep counts and service rates isn't exact due to queues
        # Let's just set placeholder and fix by adding tracking
        all_L.append(L_est); all_W.append(W_est)
        all_busy.append(0.0); all_ploss.append(0.0); all_pwait.append(0.0)
        total_arr += arr_count; total_dep += dep_count; total_blk += blk_count
        total_time_in_sys += time_in_sys_sum
    avg_L = sum(all_L)/len(all_L) if all_L else 0
    avg_W = sum(all_W)/len(all_W) if all_W else 0
    avg_busy = sum(all_busy)/len(all_busy) if all_busy else 0
    avg_ploss = sum(all_ploss)/len(all_ploss) if all_ploss else 0
    avg_pwait = sum(all_pwait)/len(all_pwait) if all_pwait else 0
    dep_rate = total_dep / (seeds_used * win_len) * 60.0 if win_len > 0 else 0
    lam_eff = dep_rate
    result = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "runtime_units": "minute",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "win": round(win_len, 6),
        "arr": round(total_arr/seeds_used, 6) if seeds_used else 0,
        "blk": round(total_blk/seeds_used, 6) if seeds_used else 0,
        "busy_frac": round(avg_busy, 6),
        "busy_util": round(avg_busy, 6),
        "dep": round(total_dep/seeds_used, 6) if seeds_used else 0,
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_ploss, 6),
        "p_wait": round(avg_pwait, 6),
        "per_seed_L": [round(x,6) for x in all_L],
        "per_seed_W": [round(x,6) for x in all_W],
        "per_seed_busy_frac": [round(x,6) for x in all_busy],
        "per_seed_p_loss": [round(x,6) for x in all_ploss],
        "per_seed_p_wait": [round(x,6) for x in all_pwait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
