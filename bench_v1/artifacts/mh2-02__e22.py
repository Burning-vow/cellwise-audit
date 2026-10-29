#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mh2-02 / 错型 E22：中途放弃(reneging)漏实现

family=customer_behaviour  expected=detectable（跑实验之前声明）
theory_ref=放弃销毁工作 ⇒ W↓、L↓；更硬的证据是计数不闭合 Σdep=Σarr-Σlost 而 lost 未上报 ⇒ J2 流量守恒直接点火。题集 v1 无声明耐心的题，故以注入方式实例化（同量级反号）
注入点：simcore 的单个 hook —— patience=abandon（其余与 REF 完全一致）
本文件与 mh2-02__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mh2-02', 'E22')
