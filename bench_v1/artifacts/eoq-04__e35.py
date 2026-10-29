#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 eoq-04 / 错型 E35：EOQ 时间单位同倍换算(年→日)

family=estimation  expected=detectable（跑实验之前声明）
theory_ref=q=√(2DS/H)：D、H 同除 365 而 S 与时间无关 ⇒ q 不变（良性）；cost=√(2DSH) 变成"元/日"，工件按"元/年"口径上报 ⇒ 差 365 倍的量纲错（J1|cost 实测 rel≈0.997，可检）。与 E28 的分界就在输出口径：E28 把 W 与 time_unit 一起换 ⇒ 内部自洽、良性；E35 只换输入侧、cost 的口径没跟着换 ⇒ 可检（10-17 由 benign 改判为 detectable，理由见 mutants.jsonl 的 relabel_reason）
注入点：simcore 的单个 hook —— time_base=annual_to_daily（其余与 REF 完全一致）
本文件与 eoq-04__REF.py 的唯一代码差是最后一行的错型代号。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('eoq-04', 'E35')
