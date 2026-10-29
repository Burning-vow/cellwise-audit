#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""外部题 ext-mm1-02 / 错型 E25：预占后剩余服务时长不更新(重头再来)

family=order  expected=detectable（跑实验之前声明）
theory_ref=中断丢弃已做工作 ⇒ 幻影工作量使 ρ_eff>ρ ⇒ W、L 同向上升（不依赖引理 A/B ⇒ 三种载体都该可检）。与 E04 的差只在 `simcore.py:585-586` 那两行（elapsed 归不归零）。带符号实测见 `DIRECTION_SIGNED.md`
注入点：simcore 的单个 hook —— discipline=lcfs_restart（其余与 REF 完全一致）
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore_ext

simcore_ext.main('ext-mm1-02', 'E25')
