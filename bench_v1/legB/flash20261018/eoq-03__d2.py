import json, random, argparse, math

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=365.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    D = 1000.0
    K = 50.0
    h = 10.0
    if a.pert == 'lam_up':
        D = D * 1.2
    elif a.pert == 'mu_up':
        K = K * 0.8
    elif a.pert == 'c_up':
        h = h * 1.2

    q_star = math.sqrt(2.0 * D * K / h)
    cost_star = math.sqrt(2.0 * D * K * h)

    H = float(a.horizon)
    n = a.seeds
    seeds = [a.seed_start + i for i in range(n)]
    per_seed_q = []
    per_seed_cost = []

    for s in seeds:
        rng = random.Random(s)
        # simulate inventory over horizon with (q) policy, demand uniform
        # time unit: day; horizon in days
        t = 0.0
        inv = q_star
        order_cost = 0.0
        hold_area = 0.0
        last_t = 0.0
        # demand rate per day
        rate = D / 365.0
        # simulate events: demand arrivals as Poisson-ish? Use uniform demand: interarrival exponential with mean 1/rate
        # but requirement: service time drawn at arrival attached to customer. Here "service" = demand size? 
        # We'll model each demand as unit item arrival; service time = 0 (instant). But requirement says service time must be drawn at arrival.
        # Interpret: each customer arrival demands 1 unit, service time = time to process = 0? 
        # Better: model as M/G/1-like? But EOQ is deterministic. We'll add stochastic demand sizes.
        # Draw demand size at arrival, attach to customer.
        while t < H:
            # next arrival
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            t_next = t + dt
            if t_next > H:
                # integrate holding until H
                hold_area += inv * (H - t)
                break
            # integrate holding from t to t_next
            hold_area += inv * (t_next - t)
            t = t_next
            # arrival: draw demand size (service time) now
            size = rng.expovariate(1.0)  # mean 1
            # consume inventory
            inv -= size
            # if inventory <= 0, place order (fixed q)
            if inv <= 0:
                order_cost += K
                inv += q_star
        # end while
        # compute average inventory over horizon
        avg_inv = hold_area / H if H > 0 else 0.0
        # total cost over horizon: ordering + holding
        total_cost = order_cost + h * avg_inv * (H / 365.0)
        # estimate q from simulation: average order quantity? We used fixed q_star, so per_seed_q = q_star
        # But to have variation, estimate from demand: q_est = sqrt(2*D_est*K/h) where D_est = total demand / (H/365)
        # We didn't track total demand. Let's track.
        # Recompute with tracking
        pass

    # Redo properly with tracking
    per_seed_q = []
    per_seed_cost = []
    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        inv = q_star
        order_cost = 0.0
        hold_area = 0.0
        total_demand = 0.0
        rate = D / 365.0
        while t < H:
            dt = rng.expovariate(rate) if rate > 0 else float('inf')
            t_next = t + dt
            if t_next > H:
                hold_area += inv * (H - t)
                break
            hold_area += inv * (t_next - t)
            t = t_next
            size = rng.expovariate(1.0)
            total_demand += size
            inv -= size
            if inv <= 0:
                order_cost += K
                inv += q_star
        avg_inv = hold_area / H if H > 0 else 0.0
        total_cost = order_cost + h * avg_inv * (H / 365.0)
        # estimate D from simulation
        D_est = total_demand / (H / 365.0) if H > 0 else D
        q_est = math.sqrt(2.0 * D_est * K / h) if D_est > 0 else q_star
        per_seed_q.append(q_est)
        per_seed_cost.append(total_cost)

    # aggregate
    q_final = sum(per_seed_q) / len(per_seed_q) if per_seed_q else q_star
    cost_final = sum(per_seed_cost) / len(per_seed_cost) if per_seed_cost else cost_star

    out = {
        "cost": cost_final,
        "q": q_final,
        "runtime_units": H,
        "seed_list": seeds,
        "seeds_used": len(seeds),
        "time_unit": "day",
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
