#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mmcK-02 / 错型 E16：把队列容量当成系统容量(少算在服务的 c 人)

family=capacity_blocking  expected=weak（跑实验之前声明）
theory_ref=阻塞条件由"N≥K"写成"waiting≥K" ⇒ 有效容量 K→K+c，高态泄漏 π_{K+1..K+c}∝ρ^K；均值二阶同样**以 π_K→0 为前提**（本族 mmcK-06 的 π_K≈0 ⇒ 属满足前提的 3 组之一）。目录里的 E17(只有队列上限没有系统上限) 在本题集语义下与 E16 同一实现，已合并（见自检声明表）
注入点：simcore 的单个 hook —— cap=queue_as_system（其余与 REF 完全一致）
本文件与 mmcK-02__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mmcK-02', 'E16')
