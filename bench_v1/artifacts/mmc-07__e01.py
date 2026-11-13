#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmc-07 / 错型 E01：FCFS→LCFS(非预占)

family=order  expected=blind（跑实验之前声明）
theory_ref=P1 恒等类，两条互不蕴含的来路（对应论文的 P1）。引理 A：定长服务 ∧ 非预占 ⇒ 离去时刻多重集不变 ⇒ N(t) 逐位恒等（dL 实测 0，残量 3.1e-4）。引理 B：泊松到达 ∧ 指数服务 ⇒ 在服务者的残存需求仍为 Exp(μ) ⇒ N 是同一条生灭链 ⇒ 均值同律（残量 2.5e-3～5.0e-3，属抽样噪声，不构成恒等）。适用边界：异质需求下“完成时刻集合与次序无关”不成立（两顾客同到、需求 1 与 10：FCFS 离去 {1,11}、LCFS {10,11}；V(t) 路径相同但 ∫N dt 是 12 对 21），因此两条引理分别按定长、指数服务陈述。载体边界：mh2 为 H2 服务，两条引理均不覆盖，其 4 件只记“幅度低于 τ*”；jackson2 由引理 C 覆盖（引理 B + Burke 可逆性，前提为站间无容量限制、无分流）。
注入点：simcore 的单个 hook —— discipline=lcfs（其余与 REF 完全一致）
本文件与 mmc-07__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmc-07', 'E01')
