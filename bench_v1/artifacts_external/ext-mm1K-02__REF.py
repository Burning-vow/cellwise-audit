#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""外部题 ext-mm1K-02：参照件（mm1K）。

真值来自 exp_2026-10-19/external/external_truth.py（独立闭式），
本文件只调用 simcore_ext 做仿真；不把 simcore 当外部真值。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore_ext

simcore_ext.main('ext-mm1K-02', 'REF')
