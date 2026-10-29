import argparse,json,heapq,random,math

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seeds",type=float,default=10)
    ap.add_argument("--horizon",type=float,default=20000.0)
    ap.add_argument("--seed-start",dest="seed_start",type=float,default=1)
    ap.add_argument("--pert",default="none")
    a=ap.parse_args()
    nseeds=int(a.seeds); H=float(a.horizon); S=int(a.seed_start)
    lam=4.0; mu=60.0/6.0; c=1.0
    if a.pert=="lam_up": lam*=1.1
    elif a.pert=="mu_up": mu*=1.1
    elif a.pert=="c_up": c=2.0
    warm=0.25*H; win=H-warm
    per_L=[];per_W=[];per_bf=[];per_pl=[];per_pw=[];seeds=[]
    totL=totW=totbf=totpl=totpw=0.0; totarr=totdep=totblk=0.0
    for k in range(nseeds):
        seed=S+k; seeds.append(seed); rng=random.Random(seed)
        t=0.0; arr_t=0.0
        q=[]; busy=False; sfree=0.0
        areaL=0.0; areaB=0.0; n_arr=0; n_dep=0; n_blk=0
        waits=[]; next_arr=0.0
        while t<H:
            next_dep=sfree if busy else float("inf")
            nxt=min(next_arr,next_dep,H)
            areaL+= (len(q)+(1 if busy else 0))*(nxt-t)
            areaB+= (1 if busy else 0)*(nxt-t)
            t=nxt
            if t==H: break
            if t==next_arr:
                st=math.log(1.0-rng.random())/mu if c==1 else math.log(1.0-rng.random())/(mu*c)
                if busy:
                    if len(q)< (c*10-1):
                        heapq.heappush(q,(t,st)); n_arr+=1
                    else:
                        n_blk+=1
                else:
                    busy=True; sfree=t+st; waits.append(0.0); n_arr+=1
                next_arr=t+math.log(1.0-rng.random())/lam
            else:
                heapq.heappush(q,(t,math.log(1.0-rng.random())/(mu*c)))
                d,s=heapq.heappop(q) if False else (None,None)
                busy=True; sfree=t+s; n_dep+=1
            # serve queue head when free handled next loop
            while busy and t>=sfree:
                n_dep+=1; busy=False
                if q:
                    at,s=heapq.heappop(q); waits.append(t-at); busy=True; sfree=t+s
        arrL=areaL; 
        w_m = warm
        # redo stats: use time-weighted but restrict via recomputation? simpler: run again skipping warmup
        per_L.append(arrL); per_bf.append(areaB)
    print(json.dumps({"note":"placeholder"}))

if __name__=="__main__": main()
