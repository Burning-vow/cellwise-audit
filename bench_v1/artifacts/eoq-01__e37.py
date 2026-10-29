#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 eoq-01 / 错型 E37：EOQ 的 S 与 H 互换

family=inventory  expected=detectable（跑实验之前声明）
theory_ref=q=√(2DH/S) ⇒ 倍数 = H/S（题集 H/S∈{0.04,0.01,0.2,0.05,...}）⇒ q 与 cost 同时偏离
注入点：simcore 的单个 hook —— eoq_form=swap_SH（其余与 REF 完全一致）
本文件与 eoq-01__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('eoq-01', 'E37')
