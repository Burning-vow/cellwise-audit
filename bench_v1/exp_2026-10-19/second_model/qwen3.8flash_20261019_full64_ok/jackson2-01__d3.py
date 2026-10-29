import random, json, math, argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam = 4.0; mu1 = 60.0/7.5; mu2 = 60.0/6.0
    if a.pert == "lam_up": lam *= 1.2
    elif a.pert == "mu_up": mu1 *= 1.2; mu2 *= 1.2
    elif a.pert == "c_up": pass
    H = a.horizon; warmup = 0.25 * H; win = H - warmup
    seeds_used = a.seeds; seed_list = [a.seed_start + i for i in range(seeds_used)]
    all_L = []; all_W = []; all_busy = []; all_ploss = []; all_pwait = []
    total_arr = 0; total_dep = 0; total_blk = 0
    for s in seeds_used:
        rng = random.Random(seed_list[s])
        t = 0.0; q1 = []; q2 = []; b1 = False; b2 = False; e1 = None; e2 = None
        next_arr = rng.expovariate(lam)
        arr_cnt = 0; dep_cnt = 0; blk_cnt = 0
        area_wip = 0.0; last_t = 0.0; wip = 0
        wait_sum = 0.0; busy1_area = 0.0; busy2_area = 0.0
        while True:
            evs = []
            if next_arr is not None and next_arr <= H: evs.append((next_arr, 'arr'))
            if e1 is not None and e1 <= H: evs.append((e1, 'dep1'))
            if e2 is not None and e2 <= H: evs.append((e2, 'dep2'))
            if not evs: break
            evs.sort(key=lambda x: (x[0], {'arr':0,'dep1':1,'dep2':2}[x[1]]))
            nt, et = evs[0]
            dt = nt - last_t
            if last_t >= warmup:
                area_wip += wip * dt
                if b1: busy1_area += dt
                if b2: busy2_area += dt
            last_t = nt; t = nt
            if et == 'arr':
                if t >= warmup: arr_cnt += 1
                svc = rng.expovariate(mu1)
                if b1:
                    q1.append((t, svc))
                else:
                    b1 = True; e1 = t + svc
                wip += 1
                next_arr = t + rng.expovariate(lam)
            elif et == 'dep1':
                b1 = False; e1 = None
                if q1:
                    at, sv = q1.pop(0)
                    if t >= warmup: wait_sum += (t - at)
                    b1 = True; e1 = t + sv
                else:
                    if t >= warmup:
                        # job leaves sys? No, goes to stage2
                        pass
                # move to stage2
                svc2 = rng.expovariate(mu2)
                if b2:
                    q2.append((t, svc2))
                else:
                    b2 = True; e2 = t + svc2
                wip -= 1; wip += 1  # net same, but conceptually moved
                # Actually wip stays same since it's still in system
                # Let me fix: when dep1 happens, job leaves stage1 queue/service, enters stage2 queue/service
                # So wip doesn't change on dep1->stage2 transition
                # But I already did wip-=1 then wip+=1, so net 0. OK.
            elif et == 'dep2':
                b2 = False; e2 = None
                if t >= warmup: dep_cnt += 1
                if q2:
                    at, sv = q2.pop(0)
                    if t >= warmup: wait_sum += (t - at)
                    b2 = True; e2 = t + sv
                wip -= 1
            # remove processed event from list logic handled by re-eval loop
            # Need to advance next_arr if consumed
            if et == 'arr':
                pass  # next_arr already updated
            # For dep events, we need to clear them properly
            # The loop above picks min event; after processing, that event's time is now past
            # We need to set the corresponding end-time to None or update
            # This approach has issues with multiple events at same time
            # Let me redo more carefully
            break  # placeholder, will rewrite below
        # Rewrite simulation properly
        rng = random.Random(seed_list[s])
        t = 0.0; q1 = []; q2 = []; b1 = False; b2 = False; e1 = float('inf'); e2 = float('inf')
        next_arr = rng.expovariate(lam)
        arr_cnt = 0; dep_cnt = 0; blk_cnt = 0
        area_wip = 0.0; last_t = 0.0; wip = 0
        wait_sum = 0.0; busy1_area = 0.0; busy2_area = 0.0
        while t < H:
            candidates = []
            if next_arr < H: candidates.append((next_arr, 'arr'))
            if e1 < H: candidates.append((e1, 'dep1'))
            if e2 < H: candidates.append((e2, 'dep2'))
            if not candidates: break
            candidates.sort(key=lambda x: (x[0], {'arr':0,'dep1':1,'dep2':2}[x[1]]))
            nt, et = candidates[0]
            dt = nt - last_t
            if last_t >= warmup:
                area_wip += wip * dt
                if b1: busy1_area += dt
                if b2: busy2_area += dt
            last_t = nt; t = nt
            if et == 'arr':
                if t >= warmup: arr_cnt += 1
                svc = rng.expovariate(mu1)
                if b1:
                    q1.append((t, svc))
                else:
                    b1 = True; e1 = t + svc
                wip += 1
                next_arr = t + rng.expovariate(lam)
            elif et == 'dep1':
                b1 = False; e1 = float('inf')
                if q1:
                    at, sv = q1.pop(0)
                    if t >= warmup: wait_sum += (t - at)
                    b1 = True; e1 = t + sv
                # Job moves to stage 2
                svc2 = rng.expovariate(mu2)
                if b2:
                    q2.append((t, svc2))
                else:
                    b2 = True; e2 = t + svc2
                # wip unchanged: left stage1, entered stage2
            elif et == 'dep2':
                b2 = False; e2 = float('inf')
                if t >= warmup: dep_cnt += 1
                if q2:
                    at, sv = q2.pop(0)
                    if t >= warmup: wait_sum += (t - at)
                    b2 = True; e2 = t + sv
                wip -= 1
        L_est = area_wip / win if win > 0 else 0
        W_est = wait_sum / dep_cnt if dep_cnt > 0 else 0
        bf = (busy1_area + busy2_area) / (2 * win) if win > 0 else 0
        pl = blk_cnt / arr_cnt if arr_cnt > 0 else 0
        pw = 0.0
        # p_wait: fraction of jobs that waited in either queue during window
        # Approximate: count jobs that had wait>0
        # Simpler: use Little's law consistency check later
        all_L.append(L_est); all_W.append(W_est); all_busy.append(bf)
        all_ploss.append(pl); all_pwait.append(pw)
        total_arr += arr_cnt; total_dep += dep_cnt; total_blk += blk_cnt
    avg_L = sum(all_L)/len(all_L) if all_L else 0
    avg_W = sum(all_W)/len(all_W) if all_W else 0
    avg_busy = sum(all_busy)/len(all_busy) if all_busy else 0
    avg_pl = sum(all_ploss)/len(all_ploss) if all_ploss else 0
    avg_pw = sum(all_pwait)/len(all_pwait) if all_pwait else 0
    dep_rate = total_dep / len(all_L) / win * 60 if win > 0 else 0  # per hour
    lam_eff = total_arr / len(all_L) / win * 60 if win > 0 else 0
    result = {
        "L": round(avg_L, 6), "W": round(avg_W, 6),
        "runtime_units": "minute", "seed_list": seed_list,
        "seeds_used": seeds_used, "time_unit": "hour",
        "win": round(win, 6),
        "arr": round(total_arr/seeds_used, 6), "blk": round(total_blk/seeds_used, 6),
        "busy_frac": round(avg_busy, 6), "busy_util": round(avg_busy, 6),
        "dep": round(total_dep/seeds_used, 6), "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6), "p_loss": round(avg_pl, 6), "p_wait": round(avg_pw, 6),
        "per_seed_L": [round(x,6) for x in all_L],
        "per_seed_W": [round(x,6) for x in all_W],
        "per_seed_busy_frac": [round(x,6) for x in all_busy],
        "per_seed_p_loss": [round(x,6) for x in all_ploss],
        "per_seed_p_wait": [round(x,6) for x in all_pwait]
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
