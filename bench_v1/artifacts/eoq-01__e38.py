#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 eoq-01 / 错型 E38：持有成本按整批计(q·H 而非 q/2·H)

family=inventory  expected=detectable（跑实验之前声明）
theory_ref=最优条件变 D/q·S=q·H ⇒ q 偏 √2 倍、成本项加倍 ⇒ q 与 cost 同时可检
注入点：simcore 的单个 hook —— eoq_form=hold_full_qty（其余与 REF 完全一致）
本文件与 eoq-01__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('eoq-01', 'E38')
