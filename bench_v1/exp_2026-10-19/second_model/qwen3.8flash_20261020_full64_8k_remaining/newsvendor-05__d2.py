import sys, json, math, random
from argparse import ArgumentParser

def main():
    p = ArgumentParser()
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--horizon', type=float, default=100.0)
    p.add_argument('--seed-start', type=int, default=42)
    p.add_argument('--pert', type=str, default='none')
    args = p.parse_args()

    mu_d = 60.0
    sigma_d = 15.0
    price = 30.0
    cost = 12.0
    salvage = 7.0
    
    cu = price - cost
    co = cost - salvage
    crit_ratio = cu / (cu + co)
    
    # Inverse CDF for standard normal approximation using erfinv
    def norm_ppf(p):
        return math.sqrt(2) * _erfinv(2*p - 1)
        
    def _erfinv(x):
        # Approximation of inverse error function
        if x == 0: return 0
        sign = 1 if x > 0 else -1
        x = abs(x)
        t = 1/(1+x*x/2)
        y = t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(t*(
