#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 jackson2-06 / 错型 E18：两节点串联丢掉第二个节点

family=routing  expected=detectable（跑实验之前声明）
theory_ref=Jackson 积式 W=W1+W2、L=L1+L2 ⇒ 丢一整项，相对缺口=W2/(W1+W2) 约 20-30%
注入点：simcore 的单个 hook —— routing=drop2nd（其余与 REF 完全一致）
本文件与 jackson2-06__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('jackson2-06', 'E18')
