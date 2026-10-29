#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""外部题 ext-mmcK-02 / 错型 E01：FCFS→LCFS(非预占)

family=order  expected=blind（跑实验之前声明）
theory_ref=P1 恒等类，两条互不蕴含的来路（《定理层_P1P2P3_正式书写_2026-10-19.md》§1/§2）。引理 A=定长 ∧ 非预占 ⇒ 离去时刻多重集不变 ⇒ N(t) 逐位恒等（dL 实测 0，残量 3.1e-4）。引理 B=泊松 ∧ 指数 ⇒ 在服务者的残存需求仍是 Exp(μ) ⇒ N 是同一条生灭链 ⇒ 均值同律（残量 2.5e-3～5.0e-3，是抽样噪声不是恒等）。⚠【10-19 作废旧句】原写"work-conserving ∧ 不读服务时长 ⇒ 完成时刻集合与次序无关 ⇒ N(t) 路径同律"是错的：异质需求下不成立（两顾客同到、需求 1 与 10：FCFS 离去 {1,11}、LCFS {10,11}；V(t) 路径相同但 ∫N dt 是 12 对 21）。载体边界：mh2 是 H2 服务，两条引理都不覆盖 ⇒ 那 4 件只能记"幅度低于 τ*、未证恒等"；jackson2 由引理 C（引理 B + Burke 可逆性，前提=站间无容量、无分流）覆盖
注入点：simcore 的单个 hook —— discipline=lcfs（其余与 REF 完全一致）
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore_ext

simcore_ext.main('ext-mmcK-02', 'E01')
