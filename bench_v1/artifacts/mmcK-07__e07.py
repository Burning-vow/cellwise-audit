#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmcK-07 / 错型 E07：λ 与 μ 互换

family=resource  expected=detectable（跑实验之前声明）
theory_ref=ρ=λ/μ→1/ρ>1 ⇒ 生灭链无上界、队长发散、W~H/2 随时域线性增长 ⇒ 小预算也查得出
注入点：simcore 的单个 hook —— rate_units=lam_mu_swap（其余与 REF 完全一致）
本文件与 mmcK-07__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmcK-07', 'E07')
