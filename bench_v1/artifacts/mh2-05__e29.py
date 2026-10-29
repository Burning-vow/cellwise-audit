#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mh2-05 / 错型 E29：加了用不上的状态变量

family=estimation  expected=benign（跑实验之前声明）
theory_ref=冗余计数不消耗 RNG、不进入任何统计 ⇒ 与 REF 逐位相同 ⇒ J1/J2/J3/J4 零报警，只用来量 J5 逐字段比的误报
注入点：simcore 的单个 hook —— state=junk（其余与 REF 完全一致）
本文件与 mh2-05__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mh2-05', 'E29')
