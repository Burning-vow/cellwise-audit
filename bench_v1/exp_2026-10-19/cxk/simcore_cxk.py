#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thin wrapper: make simcore.task_by_id() see tasks_cxk.jsonl.

The kernel itself is unchanged. The c x K artifacts import this module and
then call simcore.main(task_id, etype).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BENCH)

import simcore  # noqa: E402

TASKS = os.path.join(HERE, "tasks_cxk.jsonl")
simcore._CACHE["tb"] = {t["task_id"]: t for t in simcore.load_tasks(TASKS)}
