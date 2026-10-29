#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 jackson2-08 / 错型 E03：FCFS→SPT(读服务时长)

family=order  expected=detectable（跑实验之前声明）
theory_ref=P2 边界 2×2：读服务时长 ∧ 服务有变异 ⇒ 可检（短的先走 ⇒ N(t) 变小 ⇒ W、L 下降）；M/D/1 上变异=0 ⇒ 退化恒等，故本类不套 md1
注入点：simcore 的单个 hook —— discipline=spt（其余与 REF 完全一致）
本文件与 jackson2-08__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('jackson2-08', 'E03')
