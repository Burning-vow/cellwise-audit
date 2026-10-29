import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=2000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()
    lam = 4.0
    mu1 = 10.0
    mu2 = 10.0
    c = 1.0
    if a.pert == 'lam_up':
        lam *= 1.2
    elif a.pert == 'mu_up':
        mu1 *= 1.2
        mu2 *= 1.2
    elif a.pert == 'c_up':
        c *= 1.2
    H = float(a.horizon)
    warm = 0.25 * H
    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    seed_list = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_served = 0.0
    tot_area = 0.0
    for s in range(a.seeds):
        seed = a.seed_start + s
        seed_list.append(seed)
        rng = random.Random(seed)
        t = 0.0
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        area = 0.0
        arr = 0
        dep = 0
        blk = 0
        busy = 0.0
        wait_sum = 0.0
        served = 0
        last = 0.0
        while True:
            cand = []
            if s1 is not None:
                cand.append(s1[0])
            if s2 is not None:
                cand.append(s2[0])
            if t < H:
                cand.append(t + rng.expovariate(lam))
            if not cand:
                break
            nt = min(cand)
            if nt > H:
                nt = H
            dt = nt - t
            if t >= warm:
                area += dt * (len(q1) + len(q2) + (1 if s1 else 0) + (1 if s2 else 0))
                busy += dt * ((1 if s1 else 0) + (1 if s2 else 0))
            t = nt
            if t >= H:
                break
            if s1 is not None and s1[0] <= t:
                q2.append(s1[1])
                s1 = None
            if s2 is not None and s2[0] <= t:
                dep += 1
                s2 = None
            if s1 is None and q1:
                job = q1.pop(0)
                s1 = (t + job[1], job[1])
            if s2 is None and q2:
                job = q2.pop(0)
                s2 = (t + job[1], job[1])
            if t + 1e-12 >= last + 0 and abs(t - (last)) >= 0:
                pass
            if t < H and (not cand or t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H:
                if s1 is None or s2 is None or True:
                    pass
            if t < H and (t + 1e-12 >= min([x for x in cand if x <= t + 1e-12] or [t + 1e-12])):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
            if t < H and (t + 1e-12 >= min(cand) - 1e-12):
                pass
