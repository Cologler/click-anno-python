# -*- coding: utf-8 -*-
#
# Copyright (c) 2021~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import sys

def pytest_ignore_collect(path):
    if str(path).endswith("_py38.py"):
        return sys.version_info < (3, 8)
    return False
