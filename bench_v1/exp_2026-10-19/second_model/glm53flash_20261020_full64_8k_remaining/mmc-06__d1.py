import argparse,json,heapq,random

def run_seed(seed,H,lam,mu,c):
    rng=random.Random(seed)
    warm=0.25*H; win=H-warm
    ev=[(rng.expovariate(lam),0,'a',None)]; cnt=1
    q=[]; free=[0.0]*c; n=0
    Lsum=Bsum=0.0; prev=0.0
    arr=dep=arrw=blk=waiters=Wtot=0.0
    while ev:
        t=ev[0][0]
        if t>=H: break
        dt=t-prev
        seg=(min(t,H)-max(prev,warm))
        if seg>0: Lsum+=n*seg; Bsum+=min(n,c)*seg
        prev=t
        _,_,typ,cust=heapq.heappop(ev)
        if typ=='a':
            svc=rng.expovariate(mu)
            if t>=warm: arr+=1; arrw+=1
            nxt=t+rng.expovariate(lam)
            heapq.heappush(ev,(nxt,cnt,'a',None)); cnt+=1
            if n<c:
                heapq.heappush(ev,(t+svc,cnt,'d',(t,svc))); cnt+=1
                n+=1
            else:
                q.append((t,svc)); n+=1
        else:
            n-=1
            if t>=warm:
                dep+=1; Wtot+=t-cust[0]
            if q:
                a,s=q.pop(0)
                if a>=warm: waiters+=1
                heapq.heappush(ev,(t+s,cnt,'d',(a,s))); cnt+=1
    if H>warm:
        seg=H-max(prev,warm)
        if seg>0: Lsum+=n*seg; Bsum+=min(n,c)*seg
    L=Lsum/win; B=Bsum/win
    W=Wtot/dep if dep>0 else 0.0
    p_wait=waiters/arrw if arrw>0 else 0.0
    p_loss=0.0
    return L,W,B,p_wait,arr,dep,blk,p_loss

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seeds',type=int,default=10)
    ap.add_argument('--horizon',type=float,default=2000.0)
    ap.add_argument('--seed-start',type=int,default=1)
    ap.add_argument('--pert',default='none')
    a=ap.parse_args()
    lam=14.0; mu=60.0/6.0; c=2
    if a.pert=='lam_up': lam*=1.1
    elif a.pert=='mu_up': mu*=1.1
    elif a.pert=='c_up': c=3
    H=a.horizon
    seed_list=list(range(a.seed_start,a.seed_start+a.seeds))
    per=[run_seed(s,H,lam,mu,c) for s in seed_list]
    K=len(per)
    L=sum(p[0] for p in per)/K
    W=sum(p[1] for p in per)/K
    B=sum(p[2] for p in per)/K
    pw=sum(p[3] for p in per)/K
    arr=sum(p[4] for p in per)/K
    dep=sum(p[5] for p in per)/K
    blk=sum(p[6] for p in per)/K
    pl=sum(p[7] for p in per)/K
    pi0=None
    out={
        'L':L,'W':W,'busy_frac':B,'p_wait':pw,
        'runtime_units':a.seeds,'seed_list':seed_list,'seeds_used':K,
        'time_unit':'hour','win':H-0.25*H,
        'arr':arr,'blk':blk,'dep':dep,
        'dep_rate':dep/(H-0.25*H),'lam_eff':arr/(H-0.25*H),
        'p_loss':pl,'busy_util':B,'busy_occupied':1.0-pi0 if pi0 is not None else B,
        'per_seed_L':[p[0] for p in per],
        'per_seed_W':[p[1] for p in per],
        'per_seed_busy_frac':[p[2] for p in per],
        'per_seed_p_loss':[p[7] for p in per],
        'per_seed_p_wait':[p[3] for p in per]
    }
    print(json.dumps(out))

if __name__=='__main__': main()
