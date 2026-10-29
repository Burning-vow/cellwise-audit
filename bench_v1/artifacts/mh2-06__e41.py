#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mh2-06 / 错型 E41：顾客离开后服务台槽位不置空（资源泄漏）⇒ 队列发散

family=scheduling  expected=detectable（跑实验之前声明）
theory_ref=真实标本：`legB/flash20261018/mh2-01__d3.py:51/:86` 的 `rem` 不递减（7/192 件，L 报 36002 vs 真值 0.509）。机制：每个服务台的**第一个**顾客离开后槽位仍被占住 ⇒ c 个槽位在预热窗口结束前就全被吃掉，此后 N(t) 以 λ 线性增长、L≈λH/2 随 H 发散（预演：mm1-01 的 L 在 H=2000→8000 时 5003→19911，mmc-03 9970→39918，都是 ×4=H 的倍数 ⇒ 确实是发散而不是稳态偏移）、J2b 流量守恒 |arr−dep−blk|/arr≡1。W：窗口内**一次离开都没有** ⇒ 出口发 null、J1|W 与 J2a 记 NA（不是"检不出"，是"判不了"；这条 NaN→null 的口径修正在 `_r6` 里，旧 346 件不产生 NaN 所以对本表惰性）。可检性不靠 W：J1|L=7.5e3、J1|busy_frac=1、J1|p_wait=1.5 三条各自点火。机制计数器 trig_leak = 被泄漏的槽位数（预演实测：mm1-01 每种子 1 台、mmc-03 每种子 6 台 = c），0 才算空转。与 E06(servers=frozen1) 的分界：E06 是**配置层**把服务台数写死为 1（一开跑就少 c−1 台，读数有界），E41 是**执行层**随时间把可用台数吃到 0 台（读数随 H 发散）
注入点：simcore 的单个 hook —— sched=server_leak（其余与 REF 完全一致）
本文件与 mh2-06__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mh2-06', 'E41')
