#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 mm1-04 / 错型 E40：忙度累加变量从不置位，busy 一侧读数恒发 0

family=estimation  expected=detectable（跑实验之前声明）
theory_ref=真实标本：`legB/flash20261018/md1-01__d1.py:36` 的 `busy = 0` 之后再没被赋值 ⇒ busy_frac 精确 0。实现选择：砸的是**util 口径的源**（busy_util、busy_frac(当 busy_def=util/coincident)、busy_hw、per_seed_busy 全归 0），occupied 口径（1−π0，出自 nz 这条独立累加）保持真值。**【10-19 公开更正】** 本类第一次声明时我只把 occupied 口径猜在 mmcK 与 jackson2 上，R10c 实测把 mm1K-02/mm1K-05 判成 MISS ⇒ 声明错在题集侧：这两题的 `busy_def` 也是 `occupied`（truth_busy=0.4839/0.7558，与 ρ 不等，因阻塞使有效到达率低于 λ）。改声明后本类给出一条**14/14 无例外的分离律**：可检性完全由题集自己声明的口径决定——busy_def∈{util,coincident} 的 8 件全部 TP（J1|busy_frac rel≡1）；busy_def=occupied 的 4 件（mm1K-02/05、mmcK-03/06）全部检不出；busy_def=None（jackson2，无忙度真值）2 件全部检不出。两条仪器缺陷是这条律的成因，都要如实写：①`criteria.j3_pairing` 的门是 `... and bval`，bval=0.0 走 else ⇒ J3a 记 NA 而不是点火（预演四件的 J3a 全是 None）⇒ **"字段=0"与"字段缺失"在这条判据里不可区分**；②J2c 吃 busy_frac 但按定义 max(0,0−1)=0 永不点火（且已标 R0_VACUOUS_INTERNAL）⇒ 唯一能看到 busy_util 的腿也不响。⇒ 这不是"模型没犯错"，是**题集口径声明与判据覆盖面合起来把它藏了**。
注入点：simcore 的单个 hook —— field_const=zero_busy（其余与 REF 完全一致）
本文件与 mm1-04__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('mm1-04', 'E40')
