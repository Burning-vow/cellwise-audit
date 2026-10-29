#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mh2-05 / 错型 E11：H2 两阶段混合指数写成指数(只改二阶矩)

family=arrival_service_process  expected=detectable（跑实验之前声明）
theory_ref=P-K 只依赖 (E[S],E[S²])：均值不变、cv:1.5~3→1 ⇒ W 从 E[S](1+(1+cv²)ρ/(2(1-ρ))) 降到 E[S]/(1-ρ)，相对差=-(cv²-1)ρ/(2+(1+cv²)ρ)
注入点：simcore 的单个 hook —— service=h2_to_exp（其余与 REF 完全一致）
本文件与 mh2-05__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mh2-05', 'E11')
