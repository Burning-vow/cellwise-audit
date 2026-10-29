#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""外部题 ext-mm1K-01 / 错型 E02：FCFS→SIRO

family=order  expected=blind（跑实验之前声明）
theory_ref=同 E01 的两条来路；SIRO 的选人走辅助 RNG，不污染到达/服务流。引理 A 的可核对推论：md1 上 E01/E02 的读数**逐位相同**（max rel 均 3.14e-4/3.26e-4）⇒ 残量只来自窗口边界、与被检规则无关。反证性证据：SIRO 在 mm1/mmc 上真发生非队首选取 15.8%/47.7%
注入点：simcore 的单个 hook —— discipline=siro（其余与 REF 完全一致）
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore_ext

simcore_ext.main('ext-mm1K-01', 'E02')
