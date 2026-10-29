#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""外部题 ext-eoq-01 / 错型 E36：EOQ 根号内漏系数 2

family=inventory  expected=detectable（跑实验之前声明）
theory_ref=q=√(DS/H) 使最优处"订货成本率=持有成本率"变成比值 √2 ⇒ q 偏 1/√2、cost 偏 +（√2-1）量级
注入点：simcore 的单个 hook —— eoq_form=no_factor2（其余与 REF 完全一致）
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore_ext

simcore_ext.main('ext-eoq-01', 'E36')
