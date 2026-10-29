#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 newsvendor-03 / 错型 E31：报童 Cu/Co 用反

family=inventory  expected=detectable（跑实验之前声明）
theory_ref=临界分位 cu/(cu+co) 与 co/(cu+co) 关于 0.5 镜像 ⇒ q 从 μ+z·sd 变到 μ-z·sd；利润随之下滑
注入点：simcore 的单个 hook —— inv_opt=cuco_swap（其余与 REF 完全一致）
本文件与 newsvendor-03__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('newsvendor-03', 'E31')
