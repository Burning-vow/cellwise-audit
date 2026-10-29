import argparse, heapq, json, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--horizon", default="10000")
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    H = float(a.horizon)
    lam, mu = 7.0, 10.0
    if a.pert == "lam_up": lam = 8.4
    if a.pert == "mu_up": mu = 12.0
    if a.pert == "c_up": lam, mu = 7.0, 10.0
    T = H * 0.25
    per = {"L": [], "W": [], "busy": [], "p_loss": [], "p_wait": []}
    tot = {"arr": 0.0, "dep": 0.0, "blk": 0.0}
    seeds_used = 0
    for s in range(a.seeds):
        rng = random.Random(a.seed_start + s)
        t = 0.0
        n = 0
        evq = []
        heapq.heappush(evq, (-math.log(1 - rng.random()) / lam, 0))
        areaN = 0.0
        areaBusy = 0.0
        sumW = 0.0
        cnt = 0
        arrc = depc = blkc = 0
        waited = 0
        served = 0
        while True:
            t2, k = heapq.heappop(evq)
            if t2 > H:
                break
            areaN += n * (t2 - t)
            areaBusy += min(n, 1) * (t2 - t)
            t = t2
            if k == 0:
                arrc += 1
                st = -math.log(1 - rng.random()) / mu
                heapq.heappush(evq, (t + st, 1))
                cust = {"arr": t, "st": st}
                heapq.heappush(evq, (t, 2)) if False else None
                if t >= T:
                    served += 1
                    heapq.heappush(evq, (t + st, 3))
                    del cust
                heapq.heappush(evq, (-math.log(1 - rng.random()) / lam, 0))
        per["L"].append(0.0)
    print(json.dumps({}))
if __name__ == "__main__":
    main()
