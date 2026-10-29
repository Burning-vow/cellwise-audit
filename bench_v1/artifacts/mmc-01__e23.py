#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmc-01 / 错型 E23：换队(jockeying)漏实现

family=customer_behaviour  expected=weak（跑实验之前声明）
theory_ref=以"分队+周期换队"近似共享队：work-conserving ∧ 不读服务时长 ⇒ 均值只差换队间隔的离散化残量 ⇒ 效应小、需大预算。题集 v1 无声明换队的题，故以"近似替代"方式实例化
注入点：simcore 的单个 hook —— split=jockey（其余与 REF 完全一致）
本文件与 mmc-01__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmc-01', 'E23')
