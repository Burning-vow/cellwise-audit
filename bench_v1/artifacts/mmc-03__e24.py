#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmc-03 / 错型 E24：题面 FCFS 写成按服务时长二分类的严格优先级

family=priority  expected=detectable（跑实验之前声明）
theory_ref=非预占优先级不改总工作路径但减小 N(t)（短类先走）⇒ W、L 下降；M/D/1 上两类时长相等 ⇒ 分类读不到位次 ⇒ 退化恒等
注入点：simcore 的单个 hook —— discipline=priority_class（其余与 REF 完全一致）
本文件与 mmc-03__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmc-03', 'E24')
