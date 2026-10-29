#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmc-04 / 错型 E05：服务台数少写 1

family=resource  expected=detectable（跑实验之前声明）
theory_ref=Erlang-C Wq=C(a,c)/(cμ-λ)：c→c-1 使分母减小且 C(a,c) 上升 ⇒ W↑、L↑、busy↑
注入点：simcore 的单个 hook —— servers=minus1（其余与 REF 完全一致）
本文件与 mmc-04__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmc-04', 'E05')
