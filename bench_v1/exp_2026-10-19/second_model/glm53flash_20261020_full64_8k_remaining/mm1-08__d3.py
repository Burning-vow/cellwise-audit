import argparse, json, random, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=float, default=10)
    p.add_argument("--horizon", type=float, default=1000.0)
    p.add_argument("--seed-start", type=float, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); S = int(a.seed_start)
    lam, mu, c = 8.0, 12.0, 1.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c += 1
    warm = 0.25 * H
    per = []
    seed_list = []
    for k in range(n_seeds):
        seed = S + k
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = []
        busy_until = None
        in_sys = 0
        area_N = 0.0; area_B = 0.0
        waits = []; arr_c = 0; dep_c = 0; loss_c = 0
        served = 0; waited_n = 0
        while t < H:
            nexts = [next_arr]
            if busy_until is not None: nexts.append(busy_until)
            t1 = min(nexts)
            area_N += in_sys * (t1 - t)
            area_B += (1 if busy_until is not None else 0) * (t1 - t)
            t = t1
            if t >= H: break
            if t == next_arr:
                if t >= warm: arr_c += 1
                st = rng.expovariate(mu)
                next_arr = t + rng.expovariate(lam)
                if in_sys < c:
                    in_sys += 1
                    served += 1
                    if t >= warm:
                        waited_n += 0
                        waits.append(0.0)
                    if not queue and busy_until is None:
                        busy_until = t + st
                    else:
                        queue.append((t, st))
                elif in_sys < c + 1000000 and not queue:
                    queue.append((t, st))
                    in_sys += 1
                    served += 1
                    if t >= warm:
                        waited_n += 1
                else:
                    if t >= warm: loss_c += 1
            else:
                dep_c += 1 if t >= warm else 0
                in_sys -= 1
                if queue:
                    at, st = queue.pop(0)
                    if t >= warm:
                        waits.append(t - at)
                        waited_n += 1 if (t - at) > 0 else 0
                    busy_until = t + st
                else:
                    busy_until = None
        win = H - warm
        if arr_c == 0:
            per.append({"L":0.0,"W":0.0,"busy":0.0,"p_loss":0.0,"p_wait":0.0,"arr":0,"dep":dep_c,"blk":loss_c})
        else:
            L = area_N / win
            W = (sum(waits)/len(waits)) if waits else 0.0
            per.append({"L":L,"W":W,"busy":area_B/win,"p_loss":loss_c/arr_c,"p_wait":waited_n/arr_c,"arr":arr_c,"dep":dep_c,"blk":loss_c})
    n = len(per)
    out = {
        "L": sum(d["L"] for d in per)/n,
        "W": sum(d["W"] for d in per)/n * (60.0 if True else 1),
        "busy_frac": sum(d["busy"] for d in per)/n,
        "p_wait": sum(d["p_wait"] for d in per)/n,
        "runtime_units": H,
        "seed_list": seed_list,
        "seeds_used": n,
        "time_unit": "hour",
        "win": H - warm,
        "arr": sum(d["arr"] for d in per)/n,
        "blk": sum(d["blk"] for d in per)/n,
        "busy_util": sum(d["busy"] for d in per)/n,
        "busy_occupied": sum(d["busy"] for d in per)/n,
        "dep": sum(d["dep"] for d in per)/n,
        "dep_rate": (sum(d["dep"] for d in per)/n) / (H - warm),
        "lam_eff": lam,
        "p_loss": sum(d["p_loss"] for d in per)/n,
        "per_seed_L": [d["L"] for d in per],
        "per_seed_W": [d["W"]*60 for d in per],
        "per_seed_busy_frac": [d["busy"] for d in per],
        "per_seed_p_loss": [d["p_loss"] for d in per],
        "per_seed_p_wait": [d["p_wait"] for d in per],
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
