#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mm1-01 / 错型 E10：服务分布与题面声明相反(指数↔定长)

family=arrival_service_process  expected=detectable（跑实验之前声明）
theory_ref=P-K：Lq=λ²E[S²]/(2(1-ρ))；E[S²]: det=1/μ² vs exp=2/μ² ⇒ 二阶矩差 2 倍。md1 上方向反过来（声明定长被写成指数 ⇒ W↑）
注入点：simcore 的单个 hook —— service=invert_declared（其余与 REF 完全一致）
本文件与 mm1-01__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mm1-01', 'E10')
