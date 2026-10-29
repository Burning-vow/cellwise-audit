import json,argparse,math,random,heapq

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seeds",type=float,default=10)
    ap.add_argument("--horizon",type=float,default=2000.0)
    ap.add_argument("--seed-start",dest="seed_start",type=float,default=1)
    ap.add_argument("--pert",default="none")
    a=ap.parse_args()
    ns=int(a.seeds);H=float(a.horizon);S=int(a.seed_start)
    lam=5.0;mu=None
    m=6.0/60.0
    cv2=2.25
    p=(1+math.sqrt((cv2-1)/(cv2+1)))/2
    m1=m/(2*p);m2=m/(2*(1-p))
    warm=0.25*H;win=H-warm
    per_L=[];per_W=[];per_bf=[];per_pl=[];per_pw=[]
    seeds_used=0;seed_list=[]
    tot_arr=0;tot_dep=0;tot_blk=0
    for si in range(ns):
        sd=S+si
        rng=random.Random(sd)
        seed_list.append(sd);seeds_used+=1
        t=0.0;N=0;busy=0.0;areaN=0.0
        arr=0;dep=0;blk=0;nwait=0;swait=0.0
        q=[];inq=0
        nextarr=rng.expovariate(lam)
        depq=[]
        while t<H:
            nd=depq[0] if depq else float('inf')
            te=min(nextarr,nd,H)
            areaN+=N*(te-t)
            busy+=min(N,1)*(te-t)
            t=te
            if t>=H:break
            if t==nextarr:
                st=rng.choices([m1,m2],weights=[p,1-p])[0]
                st=rng.expovariate(1.0/st)
                arr+=1
                if N==0:
                    w=0.0
                    if t>=warm:swait+=w;nwait+=1
                    heapq.heappush(depq,t+st);N=1
                else:
                    if t>=warm:nwait+=1;swait+=1.0
                    q.append((t,st));N+=1
                nextarr=t+rng.expovariate(lam)
            else:
                heapq.heappop(depq);dep+=1;N-=1
                if q:
                    at,st=q.pop(0)
                    if at>=warm:swait+=(t-at)
                    heapq.heappush(depq,t+st);N+=1
        L=areaN/win
        waits=swait/max(nwait,1)
        bf=busy/win
        per_L.append(L);per_W.append(waits*60);per_bf.append(bf)
        per_pl.append(0.0);per_pw.append(0.0)
        tot_arr+=arr/warm*0+arr;tot_dep+=dep;tot_blk+=blk
    n=seeds_used
    out={"L":sum(per_L)/n,"W":sum(per_W)/n,"busy_frac":sum(per_bf)/n,
        "busy_util":sum(per_bf)/n,"busy_occupied":sum(per_bf)/n,
        "runtime_units":H,"seed_list":seed_list,"seeds_used":n,
        "time_unit":"hour","win":win,
        "arr":tot_arr/n,"blk":tot_blk/n,"busy_util":sum(per_bf)/n,
        "dep":tot_dep/n,"dep_rate":tot_dep/(n*win),
        "lam_eff":lam,"p_loss":0.0,"p_wait":1.0,
        "per_seed_L":per_L,"per_seed_W":per_W,
        "per_seed_busy_frac":per_bf,"per_seed_p_loss":per_pl,
        "per_seed_p_wait":per_pw}
    print(json.dumps(out))

if __name__=="__main__":
    main()
