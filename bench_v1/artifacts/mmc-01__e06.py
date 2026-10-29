#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmc-01 / 错型 E06：服务台数写死为 1

family=resource  expected=detectable（跑实验之前声明）
theory_ref=退化成 M/M/1：W=1/(μ-λ)；ρ=λ/(cμ)→λ/μ 可 ≥1 ⇒ 非稳态；J4 的"c↑⇒W↓"响应同时丢失
注入点：simcore 的单个 hook —— servers=frozen1（其余与 REF 完全一致）
本文件与 mmc-01__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmc-01', 'E06')
