#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 md1-02 / 错型 E08：服务率时钟单位写错(单侧 60×)

family=resource  expected=detectable（跑实验之前声明）
theory_ref=只把 μ 一侧除 60 ⇒ ρ=λ/μ 放大 60 倍 ⇒ ρ≥1 非稳态。与 E28 的分界：ρ 是唯一的无量纲组合，同倍不动它(良性)、单侧必动它(建模错)
注入点：simcore 的单个 hook —— rate_units=service_per_minute（其余与 REF 完全一致）
本文件与 md1-02__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('md1-02', 'E08')
