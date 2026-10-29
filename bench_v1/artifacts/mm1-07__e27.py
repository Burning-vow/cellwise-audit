#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mm1-07 / 错型 E27：离开事件重复计数

family=estimation  expected=weak（跑实验之前声明）
theory_ref=L 用面积法 ∫N dt/H ⇒ 与计数无关；W 复制样本值 ⇒ 期望无偏只增方差 ⇒ J1 全盲；破坏的是 Σarr=Σdep+Σloss ⇒ 只有 J2 查得出
注入点：simcore 的单个 hook —— counting=double_dep（其余与 REF 完全一致）
本文件与 mm1-07__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mm1-07', 'E27')
