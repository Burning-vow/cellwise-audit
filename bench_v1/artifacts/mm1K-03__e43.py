#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mm1K-03 / 错型 E43：W 不独立测量，用 Little 定律从自己报的 L 反推（自证式估计）

family=estimation  expected=blind（跑实验之前声明）
theory_ref=真实标本：`legB/flash20261018/md1-01__d2.py:103` 的 `W = L/(win_dep/win_len)`（W_not_measured 38/192 件 = 19.8%）。取 W:=L/λ̂（λ̂=dep/win 正是工件自报的 dep_rate）⇒ J2a 的 paired=dep_rate·W=L，rel 被压到**出口 _r6 的 6 位小数舍入位**（≈1e-7 相对量级）而不是参照件那种 1.2e-5 的有限窗口余项——即 J2a 对这一类**逐格恒真**。J1|W 的偏差=|L̂/λ̂−W*|/W*，闭式真值满足 L*=λW* ⇒ 它与 J1|L 是**同一个估计量**（同量级，预演实测 mm1-01：J1|W=0.0192、J1|L=0.0216，差在 λ̂ 与 λ 的抽样差，不是两回事），量级 O(1/√R)，而 τ* 的标定恰恰要求 REF 的同量级噪声不点火 ⇒ 加大预算只会更不显著。这一类的错是**方法论的**（估计量与判据同源、独立性没了），不是数值的（W 仍是一致估计）⇒ 声明 blind。它是第二型不可检：E01/E02/E20 是**定理型**（物理恒等，任何实现都躲不掉），E43 是**自证型**（判据与被验对象共用同一估计量，换一套判据就能消掉）。真实腿 B 上这 38 件没有闭式真值可比 ⇒ J2a 是唯一可用的腿 ⇒ 彻底失声，这正是"仪器盲区"而不是"模型错"
注入点：simcore 的单个 hook —— estimator=little_backsolve（其余与 REF 完全一致）
本文件与 mm1K-03__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mm1K-03', 'E43')
