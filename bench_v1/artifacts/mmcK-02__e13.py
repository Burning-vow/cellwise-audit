#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmcK-02 / 错型 E13：题面恒定泊松流被写成时变到达

family=arrival_service_process  expected=weak（跑实验之前声明）
theory_ref=W(ρ)=ρ/(μ(1-ρ)) 对 ρ 凸 ⇒ 时间平均 λ 不变但 E[W] 上升(Jensen)；ρ(1+0.25)≥1 时周期过载 ⇒ 升为可检。题集 v1 无声明时变的题，故以注入方式实例化
注入点：simcore 的单个 hook —— arrivals=timevary（其余与 REF 完全一致）
本文件与 mmcK-02__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmcK-02', 'E13')
