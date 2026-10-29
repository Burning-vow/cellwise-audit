#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmc-06 / 错型 E12：批量到达(题面单到被写成 2 人一批)

family=arrival_service_process  expected=detectable（跑实验之前声明）
theory_ref=λ_eff×2 ⇒ ρ×2 ⇒ W↑，多数题 ρ≥1 发散。题集 v1 没有声明批到达的题，"漏写批"这一方向无法实例化，故实现同一量级、符号相反的反向件
注入点：simcore 的单个 hook —— arrivals=batch（其余与 REF 完全一致）
本文件与 mmc-06__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmc-06', 'E12')
