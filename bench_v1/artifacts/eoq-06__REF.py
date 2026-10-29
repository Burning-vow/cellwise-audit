#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工件 eoq-06：正确版本（参照件）。

模板 eoq；口径：W=分钟、L=无量纲、p_loss/p_wait/busy_frac=0-1；
horizon 与 lambda、mu 同单位（年）。内核见 bench_v1/simcore.py。
用法：--seeds N --horizon H（stdout 恰好一行 JSON）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore

simcore.main('eoq-06', 'REF')
