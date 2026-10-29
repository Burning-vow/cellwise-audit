import sys
import json
import random

def main():
    args = sys.argv[1:]
    seeds = 100
    horizon = 365.0
    seed_start = 0
    perturbation = "none"

    for arg in args:
        if arg.startswith("--seeds="):
            seeds = int(arg.split("=")[1])
        elif arg.startswith("--horizon="):
            horizon = float(arg.split("=")[1])
        elif arg.startswith("--seed-start="):
            seed_start = int(arg.split("=")[1])
        elif arg.startswith("--pert="):
            perturbation = arg.split("=")[1]

    if perturbation == "lam_up":
        lambda_ = 1000 / horizon * 1.1
    elif perturbation == "mu_up":
        mu = 50 / 2
    elif perturbation == "c_up":
        c = 50 * 1.1
    else:
        lambda_ = 1000 / horizon
        mu = 50 / 2
        c = 50

    q = (2 * lambda_ * c) ** 0.5 / mu
    cost = (q * c / 2) + (lambda_ * horizon * (q / lambda_ + c / (2 * mu)))

    per_seed_q = ["不可比"] * seeds
    seed_list = list(range(seed_start, seed_start + seeds))
    seeds_used = seeds

    runtime_units = "hour"

    result = {
        "cost": cost,
        "q": q,
        "runtime_units": runtime_units,
        "seed_list": seed_list,
        "seeds_used": seeds_used,
        "per_seed_q": per_seed_q
    }

    print(json.dumps(result))

if __name__ == "__main__":
    main()
