#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mm1K-07 / 错型 E21：满员流失(baulking)动作漏实现

family=capacity_blocking  expected=weak（跑实验之前声明）
theory_ref=与 E14 行为相同、代码位不同（E14 改判定谓词、E21 删拒绝动作）⇒ P5 签名不可辨识的现成素材；均值/计数两档的可检性条件同 E14（**前提同样是 π_K→0**，不满足时均值也点火）
注入点：simcore 的单个 hook —— cap=no_baulk_action（其余与 REF 完全一致）
本文件与 mm1K-07__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mm1K-07', 'E21')
