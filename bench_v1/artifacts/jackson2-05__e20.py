#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 jackson2-05 / 错型 E20：转移矩阵/工序顺序写反(先进 2 号台)

family=routing  expected=blind（跑实验之前声明）
theory_ref=纯串联、转移概率 100% ⇒ 两节点都见泊松流 λ(Burke 定理) ⇒ W=W(λ,μ1)+W(λ,μ2) 是可交换和、L 同理 ⇒ 恒等。目录给的 detectable 在这一族不成立，声明阶段就改 blind
注入点：simcore 的单个 hook —— routing=stage_swap（其余与 REF 完全一致）
本文件与 jackson2-05__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('jackson2-05', 'E20')
