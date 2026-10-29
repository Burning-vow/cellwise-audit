import argparse,json,random,math

def run(seed,H,lam,mu,c,warm):
    r=random.Random(seed)
    t=0.0; n=0; q=0; busy=0
    tA=r.expovariate(lam); tD=float('inf')
    aN=0.0; aB=0.0; served=0; arrived=0; lost=0; waited=0; nobs=0
    wsum=0.0; nwait=0
    S=[tA]
    while True:
        t=min(S)
        if t>H: break
        dt=t-tS[0] if False else 0
        e=S.index(t)
        dt=t-prev[0]
        aN+=n*dt; aB+=min(n,1)*dt
        prev[0]=t
        if e==0:
            if n<c:
                n+=1
                if n==1:
                    S[1]=t+r.expovariate(mu)
            else:
                lost+=1
            arrived+=1
            if t>=warm: nobs+=1
            S[0]=t+r.expovariate(lam)
        else:
            n-=1; served+=1
            if n>0:
                S[1]=t+r.expovariate(mu)
            else:
                S[1]=float('inf')
        if t>=warm:
            nwait+=1
    win=H-warm
    return aN/win,aB/win,served/win,lost/win,nwait and (nwait/nobs) or 0

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--seeds',type=int,default=5)
    p.add_argument('--horizon',type=float,default=20000.0)
    p.add_argument('--seed-start',type=int,default=1)
    p.add_argument('--pert',default='none')
    a=p.parse_args()
    lam=1/15.0; mu=1/6.0; c=1
    if a.pert=='lam_up': lam*=1.1
    elif a.pert=='mu_up': mu*=1.1
    elif a.pert=='c_up': c+=1
    H=a.horizon; warm=0.25*H
    seeds=list(range(a.seed_start,a.seed_start+a.seeds))
    Ls=[];Ws=[];B=[];PL=[];PW=[]
    A=0;D=0;BL=0;U=0;PI0=0
    for s in seeds:
        L,b,dep,lost,pw=run(s,H,lam,mu,c,warm)
        Ls.append(L);B.append(b);Ws.append(None);PL.append(0.0);PW.append(pw)
        A+=1;D+=dep;BL+=lost;U+=b;PI0+=0
    Ws=[x for x in []]
    Ls,L2=Ls,Ls
    n=len(seeds)
    L=sum(Ls)/n; bu=sum(B)/n
    W=None
    out={"L":L,"W":W,"busy_frac":bu,"p_wait":sum(PW)/n,"runtime_units":H,
         "seed_list":seeds,"seeds_used":n,"time_unit":"minute","win":H-warm,
         "arr":float(n),"blk":sum(PL),"busy_util":bu,"dep":sum([]),"dep_rate":0.0,
         "lam_eff":0.0,"p_loss":0.0,
         "per_seed_L":Ls,"per_seed_W":[0.0]*n,"per_seed_busy_frac":B,
         "per_seed_p_loss":PL,"per_seed_p_wait":PW}
    print(json.dumps(out))

if __name__=="__main__":
    main()
