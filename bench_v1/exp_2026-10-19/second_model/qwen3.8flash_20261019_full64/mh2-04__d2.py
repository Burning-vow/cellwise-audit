import random, json, argparse, math

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=12345)
    p.add_argument('--pert', type=str, default='none')
    a = p.parse_args()
    
    lam_base = 5.0
    mu_base = 10.0
    cv_base = 2.0
    
    if a.pert == 'lam_up': lam_base *= 1.2
    elif a.pert == 'mu_up': mu_base *= 1.2
    elif a.pert == 'c_up': cv_base *= 1.2
    
    time_unit = 'hour'
    horizon = a.horizon
    warmup_frac = 0.25
    warmup_end = horizon * (1 - warmup_frac)
    win_len = horizon - warmup_end
    
    all_L = []
    all_W = []
    all_busy_frac = []
    all_p_loss = []
    all_p_wait = []
    per_seed_L = []
    per_seed_W = []
    per_seed_busy_frac = []
    per_seed_p_loss = []
    per_seed_p_wait = []
    total_arr = 0
    total_dep = 0
    total_blk = 0
    seeds_used = 0
    
    for i in range(a.seeds):
        seed = a.seed_start + i
        rng = random.Random(seed)
        
        # Generate service times with mean 6 min = 0.1 hour, CV=2
        # Two-stage hyperexponential: H2 with mean m, var v = (cv*m)^2
        # Choose p such that it's valid. For simplicity use Erlang-like or just sample from lognormal? 
        # Problem says two-stage mixed exponential. Let's construct one.
        # Mean = 0.1 hr, Var = (2*0.1)^2 = 0.04
        # H2: prob p of exp(rate r1), prob 1-p of exp(rate r2).
        # E[X] = p/r1 + (1-p)/r2 = 0.1
        # E[X^2] = 2p/r1^2 + 2(1-p)/r2^2 = Var + Mean^2 = 0.04 + 0.01 = 0.05
        # This is underdetermined. Pick p=0.5. Then 0.5/r1 + 0.5/r2 = 0.1 => 1/r1+1/r2=0.2
        # 1/r1^2 + 1/r2^2 = 0.1
        # Let u=1/r1, v=1/r2. u+v=0.2, u^2+v^2=0.1. uv = ((u+v)^2-(u^2+v^2))/2 = (0.04-0.1)/2 <0 impossible.
        # Need different p. Try p small. Actually let's just use a simple approximation or generate via gamma? 
        # No, must be standard library and match description. Let's use a specific H2 parameterization known to work.
        # Or simpler: since only mean and CV matter for P-K, we can simulate any distribution with those moments.
        # Let's use a shifted exponential or just sample from a distribution with correct moments using rejection?
        # Better: Use the fact that we can pick parameters. Let r1 = 1/0.05 = 20, r2 = ?
        # If we assume equal weights doesn't work. Let's try p=0.1.
        # 0.1/r1 + 0.9/r2 = 0.1
        # 0.2/r1^2 + 1.8/r2^2 = 0.05
        # This is complex. Let's just use a Gamma distribution which has mean and variance controlled, but problem says mixed exponential.
        # However, "只要均值与变异系数定了...就定了". So any dist with same mean/var works.
        # Let's use a LogNormal? No, stick to Exponential mixture.
        # A common trick: use an Erlang-k approximated by mixtures? 
        # Let's just generate service times using a method that yields mean 0.1 and var 0.04.
        # We can use a discrete approximation or just sample from Exp(mean=0.1) and adjust? No.
        # Let's use a specific H2: p=0.5, rates chosen differently? 
        # Actually, let's use a simple approach: Sample from Exp(10) [mean 0.1] and add noise? No.
        # Let's use a Gamma(shape=1/cv^2, scale=cv^2*mean) which is valid and easy. But prompt says mixed exponential.
        # I will implement a generic sampler for H2 with given mean and CV.
        # Solve for r1, r2, p. Fix p=0.5. It failed. Fix p=0.2.
        # 0.2/r1 + 0.8/r2 = 0.1
        # 0.4/r1^2 + 1.6/r2^2 = 0.05
        # Let x=1/r1, y=1/r2. 0.2x+0.8y=0.1 => x+4y=0.5 => x=0.5-4y
        # 0.4(0.5-4y)^2 + 1.6y^2 = 0.05
        # 0.4(0.25 - 4y + 16y^2) + 1.6y^2 = 0.05
        # 0.1 - 1.6y + 6.4y^2 + 1.6y^2 = 0.05
        # 8y^2 - 1.6y + 0.05 = 0
        # Discriminant: 1.6^2 - 4*8*0.05 = 2.56 - 1.6 = 0.96 > 0.
        # y = (1.6 +/- sqrt(0.96)) / 16
        # sqrt(0.96) ~ 0.98
        # y1 = (1.6+0.98)/16 = 0.16125, y2 = (1.6-0.98)/16 = 0.03875
        # x1 = 0.5 - 4*0.16125 = -0.145 (invalid)
        # x2 = 0.5 - 4*0.03875 = 0.345
        # So r1 = 1/x2 = 2.898, r2 = 1/y2 = 25.8.
        # Check: 0.2/2.898 + 0.8/25.8 = 0.069 + 0.031 = 0.1. OK.
        # Var check: 2*0.2/2.898^2 + 2*0.8/25.8^2 = 0.4/8.4 + 1.6/665 = 0.047 + 0.002 = 0.049 ~ 0.05. Close enough.
        
        p_h2 = 0.2
        r1_h2 = 2.898
        r2_h2 = 25.8
        
        def gen_service_time():
            if rng.random() < p_h2:
                return rng.expovariate(r1_h2)
            else:
                return rng.expovariate(r2_h2)
                
        events = []
        t = 0.0
        next_arrival = rng.expovariate(lam_base)
        events.append((next_arrival, 'arr'))
        
        server_free_at = 0.0
        queue = [] # list of (arrival_time, service_time)
        
        # Statistics accumulators for this seed
        area_N = 0.0
        last_t = 0.0
        N = 0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_times_sum = 0.0
        busy_time = 0.0
        
        while events:
            t, typ = events.pop(0)
            
            # Update area before changing state
            dt = t - last_t
            if last_t >= warmup_end:
                area_N += N * dt
                if N > 0:
                    busy_time += dt
            
            last_t = t
            
            if typ == 'arr':
                st = gen_service_time()
                if N == 0:
                    # Start service immediately
                    N = 1
                    server_free_at = t + st
                    events.append((server_free_at, 'dep'))
                    # Wait time is 0
                    if t >= warmup_end:
                        wait_times_sum += 0.0
                        arr_count += 1
                else:
                    # Queue or block? Single server, infinite queue assumed unless specified.
                    # Prompt mentions blk (blocked/lost). Usually M/M/1/K or similar.
                    # But prompt says "average calls L", implying stable system.
                    # With rho = 5 * 0.1 = 0.5 < 1, system is stable.
                    # Does "blk" imply finite capacity? The prompt asks for blk.
                    # Standard M/M/1 has no blocking. Maybe it refers to waiting?
                    # Or maybe the model implies a limit?
                    # "某客服热线只有 1 个坐席" -> usually infinite queue.
                    # But output requires blk. If infinite queue, blk=0.
                    # Let's assume infinite queue, so blk=0 always.
                    N += 1
                    queue.append((t, st))
                    if t >= warmup_end:
                        arr_count += 1
                
                # Schedule next arrival
                na = t + rng.expovariate(lam_base)
                events.append((na, 'arr'))
                
            elif typ == 'dep':
                if queue:
                    at, st = queue.pop(0)
                    # Service starts now
                    start_serv = t
                    end_serv = t + st
                    w = start_serv - at
                    if t >= warmup_end:
                        wait_times_sum += w
                        dep_count += 1
                    N -= 1 # One left, one enters, net change 0? No.
                    # State was N>=1. One departs. N becomes N-1.
                    # Then one enters service. N stays N-1?
                    # Wait, N includes the one in service.
                    # Before dep: N_in_system = 1 (in serv) + len(queue).
                    # After dep: 1 leaves. len(queue) decreases by 1.
                    # New head of queue enters service.
                    # So N_new = (N_old - 1).
                    # But we need to schedule departure for new service.
                    N -= 1
                    if N > 0:
                         # Next in queue starts service
                         pass
                    # Actually, logic above:
                    # If queue not empty, we pop one. That one starts service.
                    # So N remains same count?
                    # Initial: N=1 (serv), Q=[q1]. Total 2.
                    # Dep event: Serv finishes. Q pops q1. q1 starts serv.
                    # Total still 1 in serv, 0 in Q. N should be 1.
                    # My code: N-=1 makes it 0. Wrong.
                    
                    # Correction:
                    # When dep occurs:
                    # 1. Current service ends.
                    # 2. If queue non-empty, next customer starts service.
                    # 3. N decreases by 1 (the one who departed).
                    # The one starting service was already counted in N (as waiting).
                    # So N simply decrements.
                    # And we schedule its departure.
                    
                    # Re-evaluating the block:
                    # In 'arr' when N>0, we did N+=1. So waiting customers are in N.
                    # In 'dep', we remove one from system. N-=1.
                    # If queue had items, we take one out of queue and put into service.
                    # It was already in N. So N doesn't change due to transfer.
                    # Only the departure reduces N.
                    
                    # So:
                    # Pop from queue.
                    # Schedule dep for popped item.
                    # N -= 1.
                    
                    # Wait, if N=1 (only in service, queue empty).
                    # Dep happens. N becomes 0.
                    
                    # If N=2 (1 in service, 1 in queue).
                    # Dep happens. Queue pops 1. Starts service.
                    # System has 1 person (the new one in service).
                    # N should become 1.
                    # Code: N-=1 -> 1. Correct.
                    
                    # So inside 'dep':
                    # if queue:
                    #   at, st = queue.pop(0)
                    #   events.append((t+st, 'dep'))
                    # N -= 1
                    
                    # But I already did N-=1 above? No, I wrote `N -= 1` after checking queue.
                    # Let's rewrite the dep block cleanly.
                    pass
                else:
                    # No queue, server becomes idle
                    N -= 1
                    # No new service scheduled
                    if t >= warmup_end:
                        dep_count += 1
                        # Wait time for this one was 0 (it started immediately upon arrival earlier)
                        # But we don't know its arrival time here easily without storing it.
                        # We stored service time in queue, but not for current service.
                        # Need to track current service start time or arrival time.
                        # Let's store (arrival_time, service_time) for current service too?
                        # Or just calculate W based on queueing delay.
                        # For the one in service, if it arrived when N=0, wait=0.
                        # If it arrived when N>0, it was in queue, then moved to service.
                        # We need to know when it entered service.
                        
                        # Refactor: Store current_service_info = (start_time, arrival_time)
                        # On Arr: if N==0, set current_service_info=(t,t), sched dep.
                        # On Dep: if queue, pop (at, st), set current_service_info=(t, at), sched dep(t+st).
                        # Else clear current_service_info.
                        # Calculate wait = start_time - arrival_time.
                        
                        # I didn't initialize current_service_info.
                        # Let's fix the structure.
                        pass

        # Restart simulation with corrected logic
        rng = random.Random(seed)
        events = []
        t = 0.0
        next_arrival = rng.expovariate(lam_base)
        events.append((next_arrival, 'arr'))
        
        server_free_at = 0.0
        queue = [] 
        current_serv_arr_time = None
        
        area_N = 0.0
        last_t = 0.0
        N = 0
        arr_count = 0
        dep_count = 0
        blk_count = 0
        wait_times_sum = 0.0
        busy_time = 0.0
        
        while events:
            t, typ = events.pop(0)
            
            dt = t - last_t
            if last_t >= warmup_end:
                area_N += N * dt
                if N > 0:
                    busy_time += dt
            last_t = t
            
            if typ == 'arr':
                st = gen_service_time()
                if N == 0:
                    N = 1
                    current_serv_arr_time = t
                    server_free_at = t + st
                    events.append((server_free_at, 'dep'))
                    if t >= warmup_end:
                        wait_times_sum += 0.0
                        arr_count += 1
                else:
                    N += 1
                    queue.append((t, st))
                    if t >= warmup_end:
                        arr_count += 1
                
                na = t + rng.expovariate(lam_base)
                events.append((na, 'arr'))
                
            elif typ == 'dep':
                # Customer departs
                if current_serv_arr_time is not None:
                    w = t - current_serv_arr_time # Wait time = Start - Arrival. Start was when it entered service.
                    # But for the first one, start=t_arr. w=0.
                    # For queued ones, they enter service at some dep event.
                    # We need to record when they entered service.
                    # Let's change queue to store (arrival_time, service_time, entry_time?)
                    # Entry time is determined when they leave queue.
                    # Simpler: When popping from queue, we know they start service NOW (t).
                    # Their arrival time was stored.
                    # So wait = t - arrival_time.
                    
                    # But for the CURRENT departing customer, how do we know their wait?
                    # We need to have stored their arrival time when they started service.
                    # I used current
