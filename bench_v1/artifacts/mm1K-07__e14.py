#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mm1K-07 / 错型 E14：系统容量上限漏写

family=capacity_blocking  expected=weak（跑实验之前声明）
theory_ref=P3 **条件式**命题（2026-10-19 走 (a)：改句子不改标签；原句误标"P4"，P4 在同根估计量那格）。仅当被改写的约束只在**低概率状态 N=K** 生效（前提量 π_K→0）时：均值口径偏差 O(π_K·K/E[L]) 属二阶，计数口径 p_loss 的相对效应 Θ(1) 属一阶。π_K 由 M/M/c/K 的 Erlang 损失公式**从题面参数独立算出**（`P3_PRECONDITION_CHECK.py`，不许吃工件自报的 p_loss，否则退化成同源自洽）。本语料 16 组中**仅 3 组满足前提**（mmcK-06：ρ=0.2、π_K=0.0039）⇒ 实测均值偏 0.33%（<τ*=0.01，不可检）而 p_loss 偏 99.1～100%（可检）= 正面检验；其余 13 组 π_K≥1%、其中 10 组均值大幅点火（最大 rel(W)=3.215，mm1K-05 ρ=0.9、π_K=0.1602）⇒ **前提不成立，不作为本命题的检验**（不是反例）。标签维持 weak，50 件与头条四条不动
注入点：simcore 的单个 hook —— cap=none（其余与 REF 完全一致）
本文件与 mm1K-07__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mm1K-07', 'E14')
