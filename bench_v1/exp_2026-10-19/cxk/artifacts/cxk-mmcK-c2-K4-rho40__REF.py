#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""c x K sweep artifact: cxk-mmcK-c2-K4-rho40 / REF."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import simcore_cxk

simcore_cxk.simcore.main('cxk-mmcK-c2-K4-rho40', 'REF')
