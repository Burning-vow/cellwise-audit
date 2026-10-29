#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mm1-07 / 错型 E39：等待时长根本没测，出口直接发常量 0（占位赋值没换掉）

family=estimation  expected=detectable（跑实验之前声明）
theory_ref=真实标本：`legB/flash20261018/mh2-01__d3.py:84/:88` 的 `wait_area += 0.0`（该模式 12/192 件）。判据面：J1|W 的 rel=|0−W*|/W*≡1；J2a 的 paired=dep_rate·0=0 而 L>0 ⇒ rel≡1（预演 `_newop_smoke.md` (2) 四个模板都是这两个数）。**不许据此说"两条独立证据"**——两者数值都是 1.0，按 R4-2 的相对差量级判据它们不是独立格；独立性的证据只能是"来源不同"（一条吃闭式真值、一条吃内部恒等式），要在主表里分开计数才成立
注入点：simcore 的单个 hook —— field_const=zero_W（其余与 REF 完全一致）
本文件与 mm1-07__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mm1-07', 'E39')
