import random, json, argparse, sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    N, H, S, pert = a.seeds, a.horizon, a.seed_start, a.pert
    lam_base, mu1_base, mu2_base = 4.0, 60.0/7.5, 60.0/5.0
    if pert == "lam_up": lam = lam_base * 1.2; mu1 = mu1_base; mu2 = mu2_base
    elif pert == "mu_up": lam = lam_base; mu1 = mu1_base * 1.2; mu2 = mu2_base * 1.2
    elif pert == "c_up": lam = lam_base; mu1 = mu1_base; mu2 = mu2_base
    else: lam, mu1, mu2 = lam_base, mu1_base, mu2_base
    warmup_frac = 0.25
    win_start = H * warmup_frac
    time_unit = "hour"
    all_L, all_W, all_arr, all_dep, all_blk, all_busy1, all_busy2, all_ploss, all_pwait = [], [], [], [], [], [], [], [], []
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    seed_list = list(range(S, S + N))
    for si in range(N):
        rng = random.Random(seed_list[si])
        t = 0.0
        q1, q2 = [], []
        s1_free, s2_free = 0.0, 0.0
        arr_count, dep_count, blk_count = 0, 0, 0
        busy1_time, busy2_time = 0.0, 0.0
        last_event_t = 0.0
        next_arr = rng.expovariate(lam)
        events = []
        def add_event(et, typ, data=None):
            events.append((et, typ, data))
        add_event(next_arr, "arr")
        while True:
            if not events: break
            events.sort(key=lambda x: x[0])
            et, typ, data = events.pop(0)
            if et > H: break
            dt = et - last_event_t
            if last_event_t >= win_start:
                if s1_free > last_event_t: busy1_time += min(et, s1_free) - max(last_event_t, s1_free) if s1_free > last_event_t else 0
                if s2_free > last_event_t: busy2_time += min(et, s2_free) - max(last_event_t, s2_free) if s2_free > last_event_t else 0
            # simpler: track busy via state changes
            last_event_t = et
            if typ == "arr":
                arr_count += 1
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                job = {"svc1": svc1, "svc2": svc2, "t_enter": et}
                if s1_free <= et and len(q1) == 0:
                    s1_free = et + svc1
                    add_event(s1_free, "s1_done", job)
                else:
                    q1.append(job)
                nxt = et + rng.expovariate(lam)
                if nxt <= H:
                    add_event(nxt, "arr")
            elif typ == "s1_done":
                job = data
                if len(q1) > 0:
                    nj = q1.pop(0)
                    s1_free = et + nj["svc1"]
                    add_event(s1_free, "s1_done", nj)
                else:
                    s1_free = et
                if s2_free <= et and len(q2) == 0:
                    s2_free = et + job["svc2"]
                    add_event(s2_free, "s2_done", job)
                else:
                    q2.append(job)
            elif typ == "s2_done":
                job = data
                dep_count += 1
                if len(q2) > 0:
                    nj = q2.pop(0)
                    s2_free = et + nj["svc2"]
                    add_event(s2_free, "s2_done", nj)
                else:
                    s2_free = et
        # recompute busy times properly by simulating again with event-based accumulation
        # Let's redo the simulation more carefully for busy tracking
        rng = random.Random(seed_list[si])
        t = 0.0
        q1, q2 = [], []
        s1_free, s2_free = 0.0, 0.0
        arr_count, dep_count, blk_count = 0, 0, 0
        busy1_acc, busy2_acc = 0.0, 0.0
        prev_t = 0.0
        next_arr = rng.expovariate(lam)
        evts = [(next_arr, "arr", None)]
        while evts:
            evts.sort(key=lambda x: x[0])
            et, typ, data = evts.pop(0)
            if et > H: break
            dt = et - prev_t
            if prev_t >= win_start:
                if s1_free > prev_t:
                    busy1_acc += min(et, s1_free) - prev_t if s1_free > prev_t else 0
                if s2_free > prev_t:
                    busy2_acc += min(et, s2_free) - prev_t if s2_free > prev_t else 0
            prev_t = et
            if typ == "arr":
                arr_count += 1
                svc1 = rng.expovariate(mu1)
                svc2 = rng.expovariate(mu2)
                job = {"svc1": svc1, "svc2": svc2, "t_enter": et}
                if s1_free <= et and len(q1) == 0:
                    s1_free = et + svc1
                    evts.append((s1_free, "s1_done", job))
                else:
                    q1.append(job)
                nxt = et + rng.expovariate(lam)
                if nxt <= H:
                    evts.append((nxt, "arr", None))
            elif typ == "s1_done":
                job = data
                if len(q1) > 0:
                    nj = q1.pop(0)
                    s1_free = et + nj["svc1"]
                    evts.append((s1_free, "s1_done", nj))
                else:
                    s1_free = et
                if s2_free <= et and len(q2) == 0:
                    s2_free = et + job["svc2"]
                    evts.append((s2_free, "s2_done", job))
                else:
                    q2.append(job)
            elif typ == "s2_done":
                job = data
                dep_count += 1
                if len(q2) > 0:
                    nj = q2.pop(0)
                    s2_free = et + nj["svc2"]
                    evts.append((s2_free, "s2_done", nj))
                else:
                    s2_free = et
        win_len = H - win_start
        if win_len <= 0: win_len = 1e-9
        L_avg = (busy1_acc + busy2_acc) / win_len
        W_avg_min = (L_avg * win_len / max(dep_count, 1)) * 60.0 if dep_count > 0 else 0.0
        bf1 = busy1_acc / win_len if win_len > 0 else 0
        bf2 = busy2_acc / win_len if win_len > 0 else 0
        total_busy_frac = (bf1 + bf2) / 2.0
        p_loss_val = blk_count / arr_count if arr_count > 0 else 0.0
        p_wait_val = 1.0 - (dep_count / arr_count) if arr_count > 0 else 0.0
        per_seed_L.append(L_avg)
        per_seed_W.append(W_avg_min)
        per_seed_busy_frac.append(total_busy_frac)
        per_seed_p_loss.append(p_loss_val)
        per_seed_p_wait.append(p_wait_val)
        all_L.append(L_avg); all_W.append(W_avg_min); all_arr.append(arr_count); all_dep.append(dep_count); all_blk.append(blk_count)
        all_busy1.append(bf1); all_busy2.append(bf2); all_ploss.append(p_loss_val); all_pwait.append(p_wait_val)
    seeds_used = len(per_seed_L)
    avg_L = sum(all_L)/seeds_used if seeds_used else 0
    avg_W = sum(all_W)/seeds_used if seeds_used else 0
    avg_arr = sum(all_arr)/seeds_used if seeds_used else 0
    avg_dep = sum(all_dep)/seeds_used if seeds_used else 0
    avg_blk = sum(all_blk)/seeds_used if seeds_used else 0
    avg_bf1 = sum(all_busy1)/seeds_used if seeds_used else 0
    avg_bf2 = sum(all_busy2)/seeds_used if seeds_used else 0
    avg_busy_util = (avg_bf1 + avg_bf2)/2.0
    avg_ploss = sum(all_ploss)/seeds_used if seeds_used else 0
    avg_pwait = sum(all_pwait)/seeds_used if seeds_used else 0
    dep_rate = avg_dep / (H - win_start) * 3600.0 if (H - win_start) > 0 else 0.0
    lam_eff = dep_rate / 60.0 if dep_rate > 0 else 0.0
    out = {
        "L": round(avg_L, 6),
        "W": round(avg_W, 6),
        "runtime_units": "hours",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": time_unit,
        "win": round(H - win_start, 6),
        "arr": round(avg_arr, 6),
        "blk": round(avg_blk, 6),
        "busy_frac": round(avg_busy_util, 6),
        "busy_util": round(avg_busy_util, 6),
        "dep": round(avg_dep, 6),
        "dep_rate": round(dep_rate, 6),
        "lam_eff": round(lam_eff, 6),
        "p_loss": round(avg_ploss, 6),
        "p_wait": round(avg_pwait, 6),
        "per_seed_L": [round(x, 6) for x in per_seed_L],
        "per_seed_W": [round(x, 6) for x in per_seed_W],
        "per_seed_busy_frac": [round(x, 6) for x in per_seed_busy_frac],
        "per_seed_p_loss": [round(x, 6) for x in per_seed_p_loss],
        "per_seed_p_wait": [round(x, 6) for x in per_seed_p_wait]
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
