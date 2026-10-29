#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 newsvendor-02 / 错型 E34：用均值需求当订货量(忽略分位)

family=inventory  expected=detectable（跑实验之前声明）
theory_ref=q=μ_d 而非 μ_d+z·sd ⇒ Δq=z·sd（cu>co 时 z>0 ⇒ 订货不足），期望利润按凸性损失
注入点：simcore 的单个 hook —— inv_opt=mean_instead（其余与 REF 完全一致）
本文件与 newsvendor-02__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('newsvendor-02', 'E34')
