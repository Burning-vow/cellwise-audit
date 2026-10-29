import argparse,json,heapq,random
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--seeds",type=float,default=10);p.add_argument("--horizon",type=float,default=2000)
 p.add_argument("--seed-start",type=int,default=0);p.add_argument("--pert",default="none")
 a=p.parse_args();NS=int(a.seeds);H=float(a.horizon);S=int(a.seed_start)
 c=2;lam=8.0;sm=12.0/60.0
 if a.pert=="lam_up":lam*=1.1
 elif a.pert=="mu_up":sm/=1.1
 elif a.pert=="c_up":c=3
 warm=0.25*H
 psL=[];psW=[];psB=[];psPL=[];psPW=[];seed_list=[]
 for s in range(S,S+NS):
  rng=random.Random(s);seed_list.append(s)
  t=0.0;n=0;q=[];ev=[];seq=0
  heapq.heappush(ev,(rng.expovariate(lam),seq,"a",None));seq+=1
  aL=aB=aP=0.0;arr=wt=dep=0
  while ev:
   te,_,typ,dur=heapq.heappop(ev)
   if te>H:break
   lo=max(t,warm);hi=min(te,H)
   if hi>lo:
    aL+=n*(hi-lo);aB+=min(n,c)*(hi-lo)
    if n>0:aP+=(hi-lo)
   t=te
   if typ=="a":
    d=rng.expovariate(1.0/sm)
    if t>warm:arr+=1
    if n<c:
     n+=1;heapq.heappush(ev,(t+d,seq,"d",None));seq+=1
    else:
     if t>warm:wt+=1
     q.append(d)
    if t<H:heapq.heappush(ev,(t+rng.expovariate(lam),seq,"a",None));seq+=1
   else:
    n-=1
    if t>warm:dep+=1
    if q:
     n+=1;d=q.pop(0);heapq.heappush(ev,(t+d,seq,"d",None));seq+=1
  win=H-warm
  Ls=aL/win;Bs=aB/(c*win);ar=arr/win
  Ws=(Ls/ar)*60.0 if ar>0 else 0.0
  psL.append(Ls);psW.append(Ws);psB.append(Bs);psPL.append(0.0);psPW.append(wt/arr if arr>0 else 0.0)
 NS=NS;L=sum(psL)/NS;W=sum(psW)/NS;B=sum(psB)/NS;PW=sum(psPW)/NS
 dep=sum(dep for _ in [0]) if False else 0
 out={"L":L,"W":W,"busy_frac":B,"busy_util":B,"busy_occupied":sum(aP)/NS/(H-warm) if False else None,"p_wait":PW,"arr":None,"blk":0.0,"dep":None,"dep_rate":None,"lam_eff":lam,"p_loss":0.0,"per_seed_L":psL,"per_seed_W":psW,"per_seed_busy_frac":psB,"per_seed_p_loss":psPL,"per_seed_p_wait":psPW,"seed_list":seed_list,"seeds_used":NS,"time_unit":"hour","win":H*0.75,"runtime_units":"hour"}
 print(json.dumps(out))
if __name__=="__main__":main()
