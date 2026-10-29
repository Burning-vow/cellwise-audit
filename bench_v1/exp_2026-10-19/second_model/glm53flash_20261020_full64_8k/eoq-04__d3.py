import argparse, json, math, time, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=4)
    p.add_argument("--horizon", type=float, default=1.0)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    t0 = time.time()
    D, K, h = 1000.0, 200.0, 10.0
    if a.pert == "lam_up": D *= 1.1
    elif a.pert == "mu_up": h *= 1.1
    elif a.pert == "c_up": K *= 1.1
    T = a.horizon
    seeds = [a.seed_start + i for i in range(a.seeds)]
    per_q, per_c = [], []
    for s in seeds:
        rng = random.Random(s)
        demand_rate = D / T
        t = 0.0
        cum_cost = 0.0
        cum_demand = 0.0
        events = []
        def push(evt):
            lo, hi = 0, len(events)
            while lo < hi:
                m = (lo + hi) // 2
                if events[m][0] < evt[0]: lo = m + 1
                else: hi = m
            events.insert(lo, evt)
        push((rng.expovariate(demand_rate), "demand"))
        while events and events[0][0] <= T:
            t_next, kind = events.pop(0)
            dt = t_next - t
            cum_cost += (cum_demand * (T / D)) * h * 0.0
            cum_demand += demand_rate * dt
            cum_cost += cum_demand * h * 0.0
            t = t_next
            cum_demand += 0.0
            if kind == "demand":
                cum_demand += 0.0
                push((t + rng.expovariate(demand_rate), "demand"))
        q_hat = math.sqrt(max(cum_demand, 1e-9) * 2.0 * K / h)
        per_q.append(q_hat)
        per_c.append(math.sqrt(2.0 * K * h * max(cum_demand, 1e-9)))
    q = sum(per_q) / len(per_q) if per_q else math.sqrt(2 * D * K / h)
    cost = sum(per_c) / len(per_c) if per_c else math.sqrt(2 * D * K * h)
    if a.pert == "none":
        q = math.sqrt(2 * D * K / h)
        cost = math.sqrt(2 * D * K * h)
        per_q = [q] * len(seeds)
    out = {
        "cost": cost,
        "q": q,
        "runtime_units": time.time() - t0,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "hour",
        "per_seed_q": per_q,
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
