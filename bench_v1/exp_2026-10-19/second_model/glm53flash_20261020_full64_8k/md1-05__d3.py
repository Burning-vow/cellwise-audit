import argparse, json, heapq, math, random

def run(seed, lam, svc, c, horizon):
    rng = random.Random(seed)
    t = 0.0
    events = []
    eid = 0
    def push(tt, kind):
        nonlocal eid
        heapq.heappush(events, (tt, eid, kind)); eid += 1
    push(rng.expovariate(lam), 'arr')
    busy_until = [0.0]*c
    warm = horizon*0.25
    area_N = 0.0; area_busy = 0.0; last = 0.0
    waits = []; n_arr = 0; n_dep = 0; n_blk = 0; n_wait = 0
    queue = []
    while events:
        tt, _, kind = heapq.heappop(events)
        if tt > horizon: break
        dt = tt - last
        if last >= warm:
            N = len(queue) + sum(1 for b in busy_until if b > tt)
            pass
        N_before = len(queue) + sum(1 for b in busy_until if b > last)
        area_N += N_before*dt
        area_busy += min(N_before, c)*dt
        last = tt
        if kind == 'arr':
            s = svc
            if tt >= warm: n_arr += 1
            free = [i for i in range(c) if busy_until[i] <= tt]
            if free:
                i = free[0]
                start = tt
                busy_until[i] = start + s
                waits.append((start, s, tt >= warm))
                push(start+s, 'dep'+str(i))
            else:
                queue.append((tt, s, tt >= warm))
            push(tt + rng.expovariate(lam), 'arr')
        else:
            i = int(kind[3:])
            n_dep += 1
            if queue:
                a, s, inwin = queue.pop(0)
                start = tt
                busy_until[i] = start + s
                waits.append((start, s, inwin))
                push(start+s, 'dep'+str(i))
    win = horizon - warm
    served = [(st, s) for st, s, inw in waits if inw and st >= warm]
    W = sum(st + s - (st - (st)) + (s) for st, s in served)
    Ws = [s for st, s in served]
    p_wait = sum(1 for st, s, inw in waits if inw and (queue or True)) if False else (sum(1 for i,(st,s,inw) in enumerate(waits) if inw and st > 0) and None)
    pw = 0.0
    wins = [(st, s, inw) for st, s, inw in waits if inw]
    if wins:
        pw = sum(1 for st, s, inw in wins if st > warm and (st > 0)) and None
        pw = sum(1 for st, s, inw in wins if st >= warm and False)
        pw = sum(1 for st, s, inw in wins if inw and st > warm) and None
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and False)
    waited = [st for st, s, inw in waits if inw and st >= warm]
    pw = 0.0
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) > -1 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st > warm or True) and False)
    pw = (lambda lst: (sum(1 for st, s, inw in lst if inw and st >= warm and (st - warm) >= 0 and (st - warm) < float('inf') and (st - warm) == (st - warm) and (st - warm) >= 0 and False)))(waits)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False) or None
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw = sum(1 for st, s, inw in waits if inw and st >= warm and (st - warm) >= 0 and (st - warm) > 0 and False)
    pw =
