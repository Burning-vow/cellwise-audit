#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""外部题 ext-newsvendor-01 / 错型 E32：报童忽略残值(salvage 当 0)

family=inventory  expected=detectable（跑实验之前声明）
theory_ref=co=cost-salvage 变小 ⇒ 分位上升 ⇒ q↑；利润核算丢 salvage·E[(q-D)+] ⇒ q 与 exp_profit 同时偏离
注入点：simcore 的单个 hook —— inv_opt=no_salvage（其余与 REF 完全一致）
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore_ext

simcore_ext.main('ext-newsvendor-01', 'E32')
