import argparse, json, random, math, heapq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--horizon", type=float, default=2000.0)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", type=str, default="none")
    a = ap.parse_args()

    lam, mu, c, K = 6.0, 10.0, 2, 4
    if a.pert == "lam_up": lam *= 1.2
    elif a.pert == "mu_up": mu *= 1.2
    elif a.pert == "c_up": c += 1
    if K < c: K = c

    t0 = 0.25 * a.horizon
    Ls, Ws, BFs, PLs, PWs, arrs, deps, blks = [], [], [], [], [], [], [], []
    busy_utils, occs = [], []
    seed_list = []

    for si in range(a.seeds):
        seed = a.seed_start + si
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        # heap of (dep_time, id, service_time)
        busy = []
        nid = 0
        area = 0.0        # integral of N
        area_b = 0.0      # integral of min(N,c)
        area_nonempty = 0.0
        arr = dep = blk = 0
        waitsum = 0.0
        nw = 0
        arrive_t = {}
        next_arr = rng.expovariate(lam)
        while t < a.horizon:
            t_dep = busy[0][0] if busy else float("inf")
            t_next = min(next_arr, t_dep)
            t2 = min(t_next, a.horizon)
            if t2 > t0:
                area += (t2 - t) * len(busy)
                area_b += (t2 - t) * min(len(busy), c)
                if len(busy) > 0: area_nonempty += (t2 - t)
            if t_next >= a.horizon:
                t = a.horizon
                break
            t = t_next
            if next_arr <= t_dep:
                if len(busy) < K:
                    st = rng.expovariate(mu)
                    nid += 1
                    arrive_t[nid] = t
                    if len(busy) < c:
                        heapq.heappush(busy, (t + st, nid, st))
                    else:
                        # queued; store waiting customers in list
                        pass
                    # need queue handling: keep queues list
                    q.append((nid, st)) if False else None
                else:
                    blk += 1
                next_arr = t + rng.expovariate(lam)
                arr += 1
            else:
                heapq.heappop(busy)
                dep += 1
            break_flag = False
        # (reached here only via break) — restructure below
        break
    print(json.dumps({"error": "unreachable"}))
    return

if __name__ == "__main__":
    main()
