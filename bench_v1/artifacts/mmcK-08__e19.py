#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmcK-08 / 错型 E19：共享队(等价 join-shortest)写成随机分流

family=routing  expected=detectable（跑实验之前声明）
theory_ref=pooling 增益消失：分流后每支近似 M/M/1(λ/c,μ)，W=1/(μ-λ/c) > Erlang-C 的 W=1/μ+C(a,c)/(cμ-λ)
注入点：simcore 的单个 hook —— split=random（其余与 REF 完全一致）
本文件与 mmcK-08__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmcK-08', 'E19')
