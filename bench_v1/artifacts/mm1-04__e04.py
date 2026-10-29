#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mm1-04 / 错型 E04：题目要非预占却写成预占式 LCFS

family=order  expected=blind（跑实验之前声明）
theory_ref=预占破不破恒等，取决于两件事分开：① resume 保留已做工 ⇒ 工作量路径不变，但**破坏引理 A 的"非预占"前提**⇒ 定长载体可检；② 指数服务的无记忆 ⇒ 在服务的机器瞬时离去率仍是 μ ⇒ **引理 B 覆盖预占** ⇒ 均值不可检。带符号实测（`DIRECTION_SIGNED.md`，ΔW 相对同题 REF）：md1 +19.99% / +66.79%（变差）、mh2 −15.35% / −66.48%（变好）、mm1 −0.06% 与 mmc +0.06%（REF 自身 −0.11%/+0.02% ⇒ 落在噪声内，**方向不可定**）。三点与"符号 ∝ (1−cv²)"一致：cv²=0→+、cv²=1→0、cv²>1→−。⚠【10-19 作废旧公式】原写"差 = E[S]ρ(cv²−1)/(2(1−ρ))"**符号与实测相反**，且其中 LCFS-PR 的 M/G/1 均值式（E[T]=E[S]/(1−ρ)）我核不证 ⇒ 整条删除；只保留上面的带符号读数与"符号随变异方向翻转"这一实测规律，**量级未核**
注入点：simcore 的单个 hook —— discipline=lcfs_pr（其余与 REF 完全一致）
本文件与 mm1-04__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mm1-04', 'E04')
