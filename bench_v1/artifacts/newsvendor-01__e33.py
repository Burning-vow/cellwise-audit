#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 newsvendor-01 / 错型 E33：需求过程写成定长(丢掉方差)

family=inventory  expected=detectable（跑实验之前声明）
theory_ref=D≡μ_d ⇒ 利润=price·μ_d-cost·q+salvage·(q-μ_d)，缺了短缺/积压的损失项；q 来自分位数公式不受抽样影响 ⇒ "q 全对、利润偏"的部分可检格
注入点：simcore 的单个 hook —— inv_opt=demand_determ（其余与 REF 完全一致）
本文件与 newsvendor-01__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('newsvendor-01', 'E33')
