import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0 / 60.0
    mu1 = 1.0 / 7.5
    mu2 = 1.0 / 5.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu1 *= 1.2
        mu2 *= 1.2
    elif a.pert == 'c_up':
        lam *= 1.2
        mu1 *= 1.2
        mu2 *= 1.2
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = tot_dep = tot_blk = 0.0
    tot_area = 0.0
    tot_win = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        n1 = 0
        n2 = 0
        b1 = False
        b2 = False
        q1 = []
        q2 = []
        next_arr = rng.expovariate(lam)
        end1 = float('inf')
        end2 = float('inf')
        area = 0.0
        busy_area = 0.0
        wait_sum = 0.0
        served = 0
        arr_c = 0
        dep_c = 0
        blk_c = 0
        last_t = 0.0
        while t < H:
            dt = min(next_arr, end1, end2) - t
            if dt > 0:
                if t >= warm:
                    area += (n1 + n2) * dt
                    busy_area += ((1 if b1 else 0) + (1 if b2 else 0)) * dt
                t += dt
            if t >= H:
                break
            if next_arr <= t + 1e-12 and next_arr <= end1 and next_arr <= end2:
                if t >= warm:
                    arr_c += 1
                if len(q1) >= 100000:
                    if t >= warm:
                        blk_c += 1
                else:
                    st = rng.expovariate(mu1)
                    q1.append((t, st))
                    n1 += 1
                    if not b1:
                        b1 = True
                        arr_t, sv = q1.pop(0)
                        n1 -= 1
                        end1 = t + sv
                next_arr = t + rng.expovariate(lam)
            elif end1 <= t + 1e-12 and end1 <= end2:
                b1 = False
                end1 = float('inf')
                if t >= warm:
                    served += 1
                st2 = rng.expovariate(mu2)
                q2.append((t, st2))
                n2 += 1
                if not b2:
                    b2 = True
                    arr_t, sv = q2.pop(0)
                    n2 -= 1
                    end2 = t + sv
                if q1:
                    b1 = True
                    arr_t, sv = q1.pop(0)
                    n1 -= 1
                    end1 = t + sv
            else:
                b2 = False
                end2 = float('inf')
                if t >= warm:
                    dep_c += 1
                if q2:
                    b2 = True
                    arr_t, sv = q2.pop(0)
                    n2 -= 1
                    end2 = t + sv
        win = H - warm
        L = area / win if win > 0 else 0.0
        W = L / (lam * 60.0) if lam > 0 else 0.0
        bf = busy_area / (2.0 * win) if win > 0 else 0.0
        pl = blk_c / arr_c if arr_c > 0 else 0.0
        pw = 0.0
        per_L.append(L)
        per_W.append(W)
        per_bf.append(bf)
        per_pl.append(pl)
        per_pw.append(pw)
        tot_arr += arr_c
        tot_dep += dep_c
        tot_blk += blk_c
        tot_area += area
        tot_win += win
        tot_busy += busy_area
        tot_served += served
    n = a.seeds
    L = tot_area / tot_win if tot_win > 0 else 0.0
    W = L / (lam * 60.0) if lam > 0 else 0.0
    bf = tot_busy / (2.0 * tot_win) if tot_win > 0 else 0.0
    arr = tot_arr / n
    dep = tot_dep / n
    blk = tot_blk / n
    dep_rate = (tot_dep / tot_win) * 60.0 if tot_win > 0 else 0.0
    lam_eff = lam * 60.0
    p_loss = tot_blk / tot_arr if tot_arr > 0 else 0.0
    p_wait = 0.0
    out = {
        'L': L,
        'W': W,
        'runtime_units': H,
        'seed_list': seed_list,
        'seeds_used': n,
        'time_unit': 'minute',
        'win': H - warm,
        'arr': arr,
        'blk': blk,
        'busy_frac': bf,
        'busy_util': bf,
        'dep': dep,
        'dep_rate': dep_rate,
        'lam_eff': lam_eff,
        'p_loss': p_loss,
        'p_wait': p_wait,
        'per_seed_L': per_L,
        'per_seed_W': per_W,
        'per_seed_busy_frac': per_bf,
        'per_seed_p_loss': per_pl,
        'per_seed_p_wait': per_pw,
    }
    print(json.dumps(out))

if __name__ == '__main__':
    main()
