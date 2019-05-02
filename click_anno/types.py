# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from enum import Enum
from click import Choice

flag = object()

class _EnumChoice(Choice):
    def __init__(self, enum: Enum):
        self._enum = enum
        names = tuple(n.replace('_', '-') for n in enum.__members__)
        return super().__init__(names)

    def convert(self, value, param, ctx):
        enum_value = super().convert(value, param, ctx)
        enum_value = enum_value.replace('-', '_')
        return self._enum.__members__[enum_value]
