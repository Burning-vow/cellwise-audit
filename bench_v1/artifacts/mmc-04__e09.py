#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmc-04 / 错型 E09：泊松到达写成定间隔

family=arrival_service_process  expected=detectable（跑实验之前声明）
theory_ref=Kingman 近似 Wq≈λ( c_a²+ c_s² )E[S]/(2(1-ρ)) 中 c_a²:1→0 ⇒ W、L 下降；Poisson 增量独立性消失
注入点：simcore 的单个 hook —— arrivals=determ（其余与 REF 完全一致）
本文件与 mmc-04__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmc-04', 'E09')
