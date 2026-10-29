import json,argparse,heapq,random,math

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seeds",type=int,default=5)
    p.add_argument("--horizon",type=float,default=20000.0)
    p.add_argument("--seed-start",type=int,dest="seed_start",default=0)
    p.add_argument("--pert",default="none")
    a=p.parse_args()
    c=3;K=4
    lam,mu=6.0,5.0
    if a.pert=="lam_up":lam*=1.1
    elif a.pert=="mu_up":mu*=1.1
    elif a.pert=="c_up":c=4
    warm=a.horizon*0.25
    res=[]
    per_L=[];per_W=[];per_bf=[];per_pl=[];per_pw=[]
    arrs=deps=blks=0;pw_n=0
    for i in range(a.seeds):
        rng=random.Random(a.seed_start+i)
        t=0.0;n=0;departures=[]
        t_next=rng.expovariate(lam)
        aint=0.0;busy=0.0;area=0.0
        arr=dep=blk=0;waitsum=0.0;wnum=0;wnum_wait=0
        while t<a.horizon:
            td=t_next-t
            for d in list(departures):
                if d-t<td:td=d-t
            t2=t+td
            if t2>warm:
                area+=n*td
                if n>0:busy+=td
            ev=None
            if departures and departures[0]-t<=t_next-t:
                ev="dep";td=departures[0]-t
            else:ev="arr"
            t=t+td
            if ev=="arr":
                if n<K:
                    st=rng.expovariate(mu)
                    heapq.heappush(departures,t+st)
                    if t>=warm:arr+=1;wnum+=1
                    else:arr+=1
                    if n>=c:
                        if t>=warm:waitsum+=td if False else 0
                    n+=1
                    if n>c:
                        w=t+td if False else t
                if n>c:
                    pass
                n=n
                t_next=t+rng.expovariate(lam)
            else:
                heapq.heappop(departures)
                if t>=warm:dep+=1
                n-=1
            if ev=="arr" and n>=c and False:pass
            if ev=="arr":
                pass
            if ev=="arr" and n==c+1:pass
            if ev=="arr" and n>c and False:pass
        print(t,n,len(departures));break
    print(json.dumps({"ok":False}))

if __name__=="__main__":main()
