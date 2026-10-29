#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mm1-04 / 错型 E26：不去预热(warm_frac=0)

family=estimation  expected=benign（跑实验之前声明）
theory_ref=初态空系统瞬态使前段 N(t) 偏低 ⇒ L、W 系统性低估 O(1/H)；属估计口径偏差而非建模错，短预算下必偏
注入点：simcore 的单个 hook —— window=no_warm（其余与 REF 完全一致）
本文件与 mm1-04__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mm1-04', 'E26')
