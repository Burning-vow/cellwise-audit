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
    h = 10.0
    q_opt = math.sqrt(2 * K * D / h)
    cost_opt = math.sqrt(2 * K * D * h)
    seeds_used = a.seeds
    seed_list = [a.seed_start + i for i in range(seeds_used)]
    per_seed_q = []
    for s in seed_list:
        rng = random.Random(s)
        t = 0.0
        horizon = a.horizon
        if a.pert == "lam_up":
            lam_mult = 1.1
        elif a.pert == "mu_up":
            mu_mult = 1.1
        elif a.pert == "c_up":
            c_mult = 1.1
        else:
            lam_mult = 1.0
            mu_mult = 1.0
            c_mult = 1.0
        demand_rate = (D / 365.0 / 24.0) * lam_mult
        order_cost = K * c_mult
        holding_cost_per_unit_year = h * c_mult
        holding_cost_per_unit_hour = holding_cost_per_unit_year / (365.0 * 24.0)
        inv = 0.0
        last_inv_time = 0.0
        total_holding_cost = 0.0
        total_order_cost = 0.0
        warmup_end = 0.25 * horizon
        cum_demand = 0.0
        next_arrival = rng.expovariate(demand_rate) if demand_rate > 0 else float('inf')
        while t < horizon:
            dt = min(next_arrival - t, horizon - t)
            if dt < 0:
                dt = 0
            if t >= warmup_end or last_inv_time < warmup_end:
                pass
            if last_inv_time < warmup_end and t >= warmup_end:
                area = inv * (warmup_end - last_inv_time)
                total_holding_cost += area * holding_cost_per_unit_hour
                last_inv_time = warmup_end
            elif last_inv_time >= warmup_end:
                area = inv * dt
                total_holding_cost += area * holding_cost_per_unit_hour
                last_inv_time = t + dt
            t += dt
            if t >= next_arrival and next_arrival <= horizon:
                d = 1.0
                cum_demand += d
                inv -= d
                if inv < 0:
                    inv = 0
                next_arrival = t + rng.expovariate(demand_rate) if demand_rate > 0 else float('inf')
            if inv <= 0 and t < horizon:
                if t >= warmup_end:
                    total_order_cost += order_cost
                inv = q_opt
                if last_inv_time < warmup_end:
                    last_inv_time = max(last_inv_time, warmup_end)
        if last_inv_time < warmup_end:
            last_inv_time = warmup_end
        if last_inv_time < horizon:
            area = inv * (horizon - last_inv_time)
            total_holding_cost += area * holding_cost_per_unit_hour
        est_q = q_opt
        per_seed_q.append(est_q)
    out = {
        "cost": round(cost_opt, 6),
        "q": round(q_opt, 6),
        "runtime_units": "hour",
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "time_unit": "hour",
        "per_seed_q": per_seed_q
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
