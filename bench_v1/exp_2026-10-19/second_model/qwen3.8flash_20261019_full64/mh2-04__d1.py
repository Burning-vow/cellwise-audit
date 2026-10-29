import sys, json, random, argparse
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    N = a.seeds; H = a.horizon; S = a.seed_start; pert = a.pert
    lam_base = 5.0; mu_base = 10.0 # mean service time 6 min = 0.1 hr -> mu = 10/hr
    if pert == 'lam_up': lam = lam_base * 1.2
    elif pert == 'mu_up': mu = mu_base * 1.2
    elif pert == 'c_up': lam = lam_base; mu = mu_base
    else: lam = lam_base; mu = mu_base
    
    # Two-stage hyperexponential with mean 0.1 hr and CV=2
    # Let stages be Exp(mu1) and Exp(mu2) with prob p and 1-p
    # Mean = p/mu1 + (1-p)/mu2 = 0.1
    # E[S^2] = 2*p/mu1^2 + 2*(1-p)/mu2^2
    # Var(S) = E[S^2] - Mean^2. CV^2 = Var/Mean^2 = 4 => Var = 4*0.01 = 0.04
    # E[S^2] = 0.04 + 0.01 = 0.05
    # Choose simple parameters: let mu1 = 1/0.05 = 20, mu2 = 1/0.15 = 6.666...? 
    # Standard approach for HE2: pick rates such that mean and var match.
    # Let's use a known parametrization or solve numerically inside loop? No, precompute.
    # Let r1, r2 be rates. p/r1 + (1-p)/r2 = 0.1. 2p/r1^2 + 2(1-p)/r2^2 = 0.05.
    # Try r1=5, r2=20. Mean = p/5 + (1-p)/20 = 0.1. 4p + 1 - p = 2 => 3p=1 => p=1/3.
    # Check Var: E[S^2] = 2*(1/3)/25 + 2*(2/3)/400 = 2/75 + 4/1200 = 32/1200 + 4/1200 = 36/1200 = 0.03. Too low.
    # Need higher variance. Try r1=2, r2=10. Mean = p/2 + (1-p)/10 = 0.1. 5p + 1 - p = 1 => 4p=0 => p=0. Degenerate.
    # Try r1=1, r2=5. Mean = p + (1-p)/5 = 0.1. 5p + 1 - p = 0.5 => 4p = -0.5. Invalid.
    # Let's just use a generic solver or fixed valid params.
    # For CV=2, often used: p=0.5, rates such that mean=0.1, var=0.04.
    # If p=0.5, 0.5(1/r1+1/r2)=0.1 => 1/r1+1/r2=0.2.
    # 0.5(2/r1^2+2/r2^2)=0.05+0.01=0.06? No E[S^2]=Var+Mean^2=0.04+0.01=0.05.
    # 0.5(2/r1^2+2/r2^2)=0.05 => 1/r1^2+1/r2^2=0.05.
    # Let x=1/r1, y=1/r2. x+y=0.2, x^2+y^2=0.05.
    # (x+y)^2 = x^2+y^2+2xy => 0.04 = 0.05 + 2xy => xy = -0.005. Impossible for positive rates.
    # So p cannot be 0.5.
    # Let's try standard values from literature or just simulate with a distribution that fits.
    # Actually, we can sample from mixture of two exponentials.
    # Let's pick r1=10, r2=2. Mean = p/10 + (1-p)/2 = 0.1.
    # p + 5(1-p) = 1 => p + 5 - 5p = 1 => -4p = -4 => p=1. Degenerate.
    # Let's pick r1=20, r2=5. Mean = p/20 + (1-p)/5 = 0.1.
    # p + 4(1-p) = 2 => p + 4 - 4p = 2 => -3p = -2 => p=2/3.
    # Check E[S^2]: 2*(2/3)/400 + 2*(1/3)/25 = 4/1200 + 2/75 = 1/300 + 8/300 = 9/300 = 0.03. Still not 0.05.
    # We need more spread. Lower r2.
    # Let r1=50, r2=2. Mean = p/50 + (1-p)/2 = 0.1.
    # p + 25(1-p) = 5 => p + 25 - 25p = 5 => -24p = -20 => p=5/6.
    # E[S^2] = 2*(5/6)/2500 + 2*(1/6)/4 = 10/15000 + 2/24 = 1/1500 + 1/12 = 0.00066 + 0.0833 = 0.084. Too high.
    # Interpolate. Let's just use a function to generate samples matching mean/cv via rejection or approximation?
    # Simpler: Use Erlang-2? No, CV must be 2.
    # Let's use the fact that we only need mean and CV for P-K, but simulation needs actual draws.
    # I will implement a sampler for HyperExponential with parameters solved roughly or use a known set.
    # Set: p=0.2, r1=10, r2=1. Mean = 0.2/10 + 0.8/1 = 0.02+0.8=0.82. No.
    # Let's define a helper to draw from HE2 with target mean 0.1 and cv 2.
    # Parameters: p=0.5 is impossible.
    # Let's try p=0.1. 0.1/r1 + 0.9/r2 = 0.1.
    # 0.2/r1^2 + 1.8/r2^2 = 0.05.
    # This is getting complex. I'll use a pre-calculated pair:
    # Rates: 1.25 and 25. Probabilities: 0.9 and 0.1.
    # Mean = 0.9/1.25 + 0.1/25 = 0.72 + 0.004 = 0.724. No.
    # Correct pair for Mean=1, CV=2: p=0.5, rates 0.2679 and 3.732? No.
    # Let's just use a generic exponential with adjusted rate? No, CV=1.
    # I will use a mixture of two exponentials with parameters derived from:
    # Let alpha = 0.5, beta1 = 1/(mean*(1+cv)), beta2 = 1/(mean*(1-cv))? No.
    # I'll hardcode a valid HE2 distribution for Mean=0.1, CV=2.
    # From online calculators: p=0.5, lambda1=1.333, lambda2=0.666? Mean=0.5/1.33+0.5/0.66=0.375+0.75=1.125.
    # Let's use: p=0.5, rates 5 and 1. Mean=0.5/5+0.5/1=0.1+0.5=0.6.
    # Okay, I will implement a simple rejection sampling or just use a Gamma distribution approximated by sum of exps?
    # Actually, for the code, I'll use a specific HE2:
    # p = 0.5, r1 = 10, r2 = 2.5. Mean = 0.05 + 0.2 = 0.25.
    # Let's scale. Target Mean 0.1.
    # Let's use r1=20, r2=5, p=0.5. Mean=0.025+0.1=0.125. Close.
    # Let's use r1=25, r2=5, p=0.5. Mean=0.02+0.1=0.12.
    # Let's use r1=30, r2=5, p=0.5. Mean=0.0166+0.1=0.1166.
    # Let's use r1=40, r2=5, p=0.5. Mean=0.0125+0.1=0.1125.
    # Let's use r1=50, r2=5, p=0.5. Mean=0.01+0.1=0.11.
    # Let's use r1=100, r2=5, p=0.5. Mean=0.005+0.1=0.105.
    # Let's use r1=200, r2=5, p=0.5. Mean=0.0025+0.1=0.1025.
    # Let's use r1=400, r2=5, p=0.5. Mean=0.00125+0.1=0.10125.
    # It converges to 0.1 as r1->inf. But CV changes.
    # I will use a proper solver in the code? No, too long.
    # I'll use a known valid set: p=0.5, rates 1.333 and 0.666 scaled?
    # Let's just use an Exponential distribution with rate 10 (Mean 0.1, CV 1). The problem says "two-stage mixed exponential... mean 6 min, CV 2".
    # Wait, if I use CV=1, the results W and L will be different.
    # I must respect CV=2.
    # I will use a mixture: 50% Exp(rate=20), 50% Exp(rate=2).
    # Mean = 0.5/20 + 0.5/2 = 0.025 + 0.25 = 0.275. Scale down by 2.75.
    # Rates: 20/0.275 = 72.7, 2/0.275 = 7.27.
    # Mean = 0.5/72.7 + 0.5/7.27 = 0.0068 + 0.068 = 0.075. Not 0.1.
    # Let's find exact parameters for Mean=0.1, CV=2.
    # Let p=0.5. 0.5(1/r1+1/r2)=0.1 => 1/r1+1/r2=0.2.
    # 0.5(2/r1^2+2/r2^2)=0.05 => 1/r1^2+1/r2^2=0.05.
    # As shown before, this has no real solution.
    # Try p=0.2. 0.2/r1 + 0.8/r2 = 0.1.
    # 0.4/r1^2 + 1.6/r2^2 = 0.05.
    # Let u=1/r1, v=1/r2. 0.2u+0.8v=0.1 => u+4v=0.5 => u=0.5-4v.
    # 0.4(0.5-4v)^2 + 1.6v^2 = 0.05.
    # 0.4(0.25 - 4v + 16v^2) + 1.6v^2 = 0.05.
    # 0.1 - 1.6v + 6.4v^2 + 1.6v^2 = 0.05.
    # 8v^2 - 1.6v + 0.05 = 0.
    # Discriminant: 1.6^2 - 4*8*0.05 = 2.56 - 1.6 = 0.96 > 0.
    # v = (1.6 +/- sqrt(0.96)) / 16.
    # sqrt(0.96) ~ 0.98.
    # v1 = 2.58/16 = 0.161. u1 = 0.5 - 4(0.161) = 0.5 - 0.644 < 0. Invalid.
    # v2 = 0.62/16 = 0.03875. u2 = 0.5 - 4(0.03875) = 0.5 - 0.155 = 0.345.
    # r1 = 1/u2 = 2.9. r2 = 1/v2 = 25.8.
    # So p=0.2, rates 2.9 and 25.8.
    # I will use these approximate rates.
    
    def get_service_time(rng):
        if rng.random() < 0.2:
            return rng.expovariate(2.9)
        else:
            return rng.expovariate(25.8)

    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    
    total_arr = 0
    total_dep = 0
    total_blk = 0
    total_busy_time = 0.0
    total_wait_time = 0.0
    total_system_time = 0.0 # Sum of times spent in system by all customers
    
    win_len = H * 0.75 # Remove first 25%
    warmup_end = H * 0.25
    
    seed_list = []
    
    for i in range(N):
        seed = S + i
        seed_list.append(seed)
        rng = random.Random(seed)
        
        t = 0.0
        next_arr = rng.expovariate(lam)
        queue = [] # List of arrival times
        busy_until = 0.0
        
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_sum = 0.0
        sys_time_sum = 0.0
        busy_integral = 0.0
        last_event_t = 0.0
        current_state_busy = False
        
        # We need to track state changes for integration
        # State: 0=idle, 1=busy
        # We integrate area under curve of min(N(t), 1) which is 1 if busy, 0 if idle.
        
        while t < H:
            # Determine next event
            if queue:
                next_dep = busy_until
            else:
                next_dep = float('inf')
            
            next_evt = min(next_arr, next_dep)
            
            if next_evt > H:
                break
                
            # Integrate busy fraction up to next_evt
            dt = next_evt - t
            if current_state_busy:
                busy_integral += dt
            
            t = next_evt
            
            if t == next_arr:
                # Arrival
                arr_count += 1
                st = get_service_time(rng)
                
                if len(queue) == 0 and not current_state_busy:
                    # Start service immediately
                    current_state_busy = True
                    busy_until
