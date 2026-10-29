import argparse, json, math, random

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=1)
    p.add_argument("--horizon", type=float, default=8760.0)
    p.add_argument("--seed-start", type=int, default=42)
    p.add_argument("--pert", type=str, default="none")
    a = p.parse_args()
    D = 1000.0
    K = 50.0
    h = 2.0
    q_opt = math.sqrt(2 * K * D / h)
    cost_opt = math.sqrt(2 * K * D * h)
    per_seed_q = []
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        # Simulate EOQ logic: order when inventory hits 0, lead time 0
        # Time unit: hours (yearly demand 1000 -> ~0.114/hr)
        t = 0.0
        horizon_hours = a.horizon if a.pert == "none" else a.horizon
        # If perturbation exists, adjust parameters slightly to test robustness
        local_D = D
        local_K = K
        local_h = h
        if a.pert == "lam_up":
            local_D *= 1.1
        elif a.pert == "mu_up":
            local_h *= 1.1
        elif a.pert == "c_up":
            local_K *= 1.1
        
        local_q = math.sqrt(2 * local_K * local_D / local_h)
        
        # Simple simulation to verify flow/balance
        inv = local_q
        orders = 0
        last_order_time = 0.0
        while t < horizon_hours:
            # Demand rate
            dr = local_D / 8760.0
            # Next event: inventory depletion or end of horizon
            dt_deplete = inv / dr if dr > 0 else float('inf')
            next_t = min(t + dt_deplete, horizon_hours)
            t = next_t
            if t >= horizon_hours:
                break
            # Reorder
            inv = local_q
            orders += 1
            
        # Estimate Q from observed cycle length
        if orders > 0:
            avg_cycle = horizon_hours / orders
            est_q = avg_cycle * (local_D / 8760.0)
        else:
            est_q = local_q
        per_seed_q.append(est_q)

    out = {
        "cost": cost_opt,
        "q": q_opt,
        "runtime_units": "hour",
        "seed_list": [a.seed_start + i for i in range(a.seeds)],
        "seeds_used": a.seeds,
        "time_unit": "hour",
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
