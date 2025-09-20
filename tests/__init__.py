#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Prepare environment for running `pytest`

see copyright/license https://github.com/senzing-garage/sz-semantics/README.md
"""

import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
