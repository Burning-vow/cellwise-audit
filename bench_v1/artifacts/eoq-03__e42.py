#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 eoq-03 / 错型 E42：需求率从自己数出的订货次数反推，丢掉不满一轮的那一段

family=numerics  expected=weak（跑实验之前声明）
theory_ref=真实标本：`legB/flash20261018/eoq-02__d1.py:60` 的 `est_q = D*(span/365.0)/orders`——闭式 q* 算对了，但出口报的是"仿真窗口里数出的次数"反推出来的 q̂。取一年窗口、orders=⌊D/q*⌋ ⇒ q̂/q*=√(⌊D/q*⌋/(D/q*))=√(1−frac/(D/q*)) ⇒ **偏差只由周期数是否落在整数上决定，与样本预算无关**。题集 6 题解析预算（D/q*, ⌊⌋, δq, δcost）：eoq-01 (4.4721,4,5.4258%,0.1555%)、eoq-02 (2.2361,2,5.4258%,0.1555%)、eoq-03 (10.0,10,**0,0**)、eoq-04 (5.0,5,**0,0**)、eoq-05 (10.0,10,**0,0**)、eoq-06 (5.0,5,**0,0**) ⇒ 4/6 件偏差**精确为 0**（trig_lostcycle=0 ⇒ 按 INJECTION_IDLE 剔除，不进任何分母），活的 2 件里 q 偏 5.43% > τ*=0.01 可检、cost 偏 0.156% < τ* 不可检（EOQ 成本曲线在最优点右侧二次平坦：δcost≈δq²/2）⇒ 这是"一个工件两个观测量、判决相反"的现成格。⚠ 真实那 2 件的形态是 `while True` 永不退出（run=EXC/timeout），**根本进不了判据分母**，落链条的 CRASH/TIMEOUT 档；本算子建模的是"循环退出了并把未收敛值报出来"那一支，不是全部
注入点：simcore 的单个 hook —— solver=rate_from_own_order_count（其余与 REF 完全一致）
本文件与 eoq-03__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('eoq-03', 'E42')
