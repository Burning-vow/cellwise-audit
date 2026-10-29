import argparse, json, heapq, math, random

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=float, default=5)
    ap.add_argument("--horizon", type=float, default=4000.0)
    ap.add_argument("--seed-start", type=float, default=1)
    ap.add_argument("--pert", default="none")
    a = ap.parse_args()
    n_seeds = int(a.seeds); H = float(a.horizon); s0 = int(a.seed_start)
    c = 2; lam = 8.0/60.0; mu = 1.0/6.0
    if a.pert == "lam_up": lam *= 1.1
    elif a.pert == "mu_up": mu *= 1.1
    elif a.pert == "c_up": c = 3
    warm = 0.25 * H
    pL=[];pW=[];pBF=[];pPW=[];pPL=[];seeds=[]
    tL=tW=tBF=tPW=tPL=0.0; cL=cW=cBF=cPW=cPL=0.0; aL=dL=0.0
    for k in range(n_seeds):
        seed = s0 + k
        seeds.append(seed)
        rng = random.Random(seed)
        t = 0.0; n = 0; t_next = rng.expovariate(lam)
        busy_area = 0.0; area = 0.0
        waits = 0; arrs = 0; deps = 0; losses = 0
        sL=sW=sBF=sPW=sPL=0.0; cntL=cntW=cntBF=cntPW=cntPL=0
        arrived = []
        busy = []
        ev = []
        heapq.heappush(ev, (t_next, "a"))
        while ev:
            t, typ = heapq.heappop(ev)
            if t > H: break
            dt = t - last_t if (last_t := ev_prev[0]) else 0
            pass
        ev_prev = 0.0
        pass
    print(json.dumps({}))

if __name__ == "__main__":
    main()
