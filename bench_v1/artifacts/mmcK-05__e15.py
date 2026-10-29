#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmcK-05 / 错型 E15：容量少 3(K→K-3)

family=capacity_blocking  expected=weak（跑实验之前声明）
theory_ref=同 E14 的条件式写法。ρ<1 时 π_K∝ρ^K，K 减小使 p_loss 指数上升；均值二阶**只在 π_K→0 时成立**。⚠ 本族在 mmcK-06 上 K−3=1 < c=3 属退化参数 ⇒ π_K 不可算，该组按 NA 留名（不许静默丢行、也不许当 0）
注入点：simcore 的单个 hook —— cap=minus3（其余与 REF 完全一致）
本文件与 mmcK-05__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmcK-05', 'E15')
