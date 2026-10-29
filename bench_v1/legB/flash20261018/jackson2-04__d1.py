import json, random, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=5)
    ap.add_argument('--horizon', type=float, default=1000.0)
    ap.add_argument('--seed-start', type=int, default=1)
    ap.add_argument('--pert', type=str, default='none')
    a = ap.parse_args()

    lam = 4.0
    mu1 = 10.0
    mu2 = 12.0
    if a.pert == 'lam_up':
        lam = 4.8
    elif a.pert == 'mu_up':
        mu1 = 12.0
        mu2 = 14.4
    elif a.pert == 'c_up':
        lam = 4.8
        mu1 = 12.0
        mu2 = 14.4

    H = float(a.horizon)
    warm = 0.25 * H
    seeds = [a.seed_start + i for i in range(a.seeds)]

    per_L = []
    per_W = []
    per_bf = []
    per_pl = []
    per_pw = []
    tot_arr = 0.0
    tot_dep = 0.0
    tot_blk = 0.0
    tot_busy = 0.0
    tot_wait = 0.0
    tot_soj = 0.0
    tot_win = 0.0

    for s in seeds:
        rng = random.Random(s)
        t = 0.0
        q1 = []
        q2 = []
        s1 = None
        s2 = None
        n_arr = 0
        n_dep = 0
        n_blk = 0
        busy = 0.0
        soj = 0.0
        wait = 0.0
        last = 0.0
        while True:
            if s1 is None and q1:
                s1 = q1.pop(0)
                s1['start'] = t
            if s2 is None and q2:
                s2 = q2.pop(0)
                s2['start'] = t
            cands = []
            if s1 is not None:
                cands.append(s1['start'] + s1['svc'])
            if s2 is not None:
                cands.append(s2['start'] + s2['svc'])
            if t < H:
                cands.append(t + rng.expovariate(lam))
            if not cands:
                break
            nt = min(cands)
            if nt > H:
                nt = H
            dt = nt - t
            if t >= warm:
                soj += dt * (len(q1) + len(q2) + (1 if s1 else 0) + (1 if s2 else 0))
                busy += dt * ((1 if s1 else 0) + (1 if s2 else 0))
            t = nt
            if s1 is not None and t >= s1['start'] + s1['svc']:
                q2.append(s1)
                s1 = None
            if s2 is not None and t >= s2['start'] + s2['svc']:
                n_dep += 1
                if t >= warm:
                    wait += t - s2['arr']
                s2 = None
            if t < H and abs(t - (last + 0)) >= 0:
                pass
            if t < H:
                pass
            if t < H and (s1 is None or s2 is None or True):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t >= 0):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t < H:
                pass
            if t < H and (t == nt):
                pass
            if t
