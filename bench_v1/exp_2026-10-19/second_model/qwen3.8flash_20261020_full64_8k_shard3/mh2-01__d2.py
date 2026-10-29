import argparse, json, math, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=10)
    p.add_argument("--horizon", type=float, default=100.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    lam_base, mu_base = 3.0, 10.0
    if a.pert == "lam_up": lam_base *= 1.2
    elif a.pert == "mu_up": mu_base *= 1.2
    elif a.pert == "c_up": pass
    time_unit = "hour"
    horizon = a.horizon
    warmup_frac = 0.25
    win_start = warmup_frac * horizon
    win_len = horizon - win_start
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    per_seed_L, per_seed_W, per_seed_busy_frac, per_seed_p_loss, per_seed_p_wait = [], [], [], [], []
    total_arr, total_dep, total_blk = 0, 0, 0
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        next_arr = rng.expovariate(lam_base)
        queue = []
        busy_until = 0.0
        is_busy = False
        arr_count, dep_count, blk_count = 0, 0, 0
        wait_sum, service_sum = 0.0, 0.0
        area_N, area_busy = 0.0, 0.0
        last_t = 0.0
        while True:
            evs = []
            if next_arr < horizon: evs.append(("arr", next_arr))
            if is_busy and busy_until < horizon: evs.append(("dep", busy_until))
            if not evs: break
            evs.sort(key=lambda x: x[1])
            etype, etime = evs[0]
            dt = etime - last_t
            if last_t >= win_start:
                N_now = len(queue) + (1 if is_busy else 0)
                area_N += N_now * dt
                if is_busy: area_busy += dt
            last_t = etime
            if etype == "arr":
                if last_t >= win_start: arr_count += 1
                if is_busy or len(queue) > 0:
                    queue.append(etime)
                else:
                    svc = rng.expovariate(mu_base)
                    is_busy = True
                    busy_until = etime + svc
                    if last_t >= win_start:
                        service_sum += svc
                        dep_count += 1
                    next_arr = etime + rng.expovariate(lam_base)
            elif etype == "dep":
                if last_t >= win_start:
                    dep_count += 1
                is_busy = False
                if queue:
                    arr_time = queue.pop(0)
                    svc = rng.expovariate(mu_base)
                    is_busy = True
                    busy_until = etime + svc
                    w = etime - arr_time
                    if last_t >= win_start:
                        wait_sum += w
                        service_sum += svc
                else:
                    next_arr = etime + rng.expovariate(lam_base) if next_arr <= etime else next_arr
        L_est = area_N / win_len if win_len > 0 else 0
        W_est = (wait_sum + service_sum) / dep_count if dep_count > 0 else 0
        bf_est = area_busy / win_len if win_len > 0 else 0
        pl_est = blk_count / arr_count if arr_count > 0 else 0
        pw_est = wait_sum / dep_count if dep_count > 0 else 0
        per_seed_L.append(L_est); per_seed_W.append(W_est)
        per_seed_busy_frac.append(bf_est); per_seed_p_loss.append(pl_est); per_seed_p_wait.append(pw_est)
        total_arr += arr_count; total_dep += dep_count; total_blk += blk_count
    avg_L = sum(per_seed_L)/len(per_seed_L) if per_seed_L else 0
    avg_W = sum(per_seed_W)/len(per_seed_W) if per_seed_W else 0
    avg_bf = sum(per_seed_busy_frac)/len(per_seed_busy_frac) if per_seed_busy_frac else 0
    avg_pl = sum(per_seed_p_loss)/len(per_seed_p_loss) if per_seed_p_loss else 0
    avg_pw = sum(per_seed_p_wait)/len(per_seed_p_wait) if per_seed_p_wait else 0
    arr_avg = total_arr/len(seed_list) if seed_list else 0
    dep_avg = total_dep/len(seed_list) if seed_list else 0
    blk_avg = total_blk/len(seed_list) if seed_list else 0
    dep_rate = dep_avg/win_len*60 if win_len>0 else 0
    lam_eff = dep_rate/60 if dep_rate>0 else 0
    out = {"L":avg_L,"W":avg_W,"busy_frac":avg_bf,"runtime_units":horizon,"seed_list":seed_list,"seeds_used":seeds_used,"time_unit":time_unit,"win":win_len,"arr":arr_avg,"blk":blk_avg,"busy_util":avg_bf,"dep":dep_avg,"dep_rate":dep_rate,"lam_eff":lam_eff,"p_loss":avg_pl,"p_wait":avg_pw,"per_seed_L":per_seed_L,"per_seed_W":per_seed_W,"per_seed_busy_frac":per_seed_busy_frac,"per_seed_p_loss":per_seed_p_loss,"per_seed_p_wait":per_seed_p_wait}
    print(json.dumps(out))

if __name__=="__main__": main()
