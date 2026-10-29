#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mm1K-03 / 错型 E28：时间单位小时->分钟(率同除60、时域同乘60、输出口径同步换算)

family=estimation  expected=benign（跑实验之前声明）
theory_ref=ρ=λ/μ 不变 ⇒ N(t) 的律不变 ⇒ L、busy、p_loss、p_wait 与 REF 同分布；输出口径也一起换算(W 同乘 60、time_unit 写 minute) ⇒ 按题集契约判 J1|W 实测 rel=1.1e-3 < τ*=0.01，**不报警**（读数出自 MUTANT_MATRIX_R10b.shard1.csv 的 mm1-02__E28；10-17 之前这一格写的是"工件没回乘 ⇒ J1-W 报警＝量纲假阳"，与矩阵读数矛盾，已按实测更正）。件仍属良性，但它是"单位自愈能把假阳藏起来"的标本：判分时把单位钉死 ⇒ J2a 由 1e-5 跳到 0.9833，见 UNIT_HEALING_EXPOSURE.md；堵法见 criteria.j0_unit_anchor
注入点：simcore 的单个 hook —— time_base=scale60（其余与 REF 完全一致）
本文件与 mm1K-03__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mm1K-03', 'E28')
