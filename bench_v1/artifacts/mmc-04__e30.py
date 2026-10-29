#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmc-04 / 错型 E30：预热窗口写成"全部时间的一半"

family=estimation  expected=benign（跑实验之前声明）
theory_ref=warm_frac 0.25→0.5 只减少样本量（方差↑），不改稳态期望 ⇒ 与 REF 同分布、CI 更宽
注入点：simcore 的单个 hook —— window=warm_half（其余与 REF 完全一致）
本文件与 mmc-04__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmc-04', 'E30')
