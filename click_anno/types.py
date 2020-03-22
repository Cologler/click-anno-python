# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from enum import Enum
from click import Choice, ParamType

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

_PARAM_TYPE_MAP = {}

def register_param_type(annotation: type, param_type: ParamType):
    '''
    register a instance of `click.ParamType` for the annotation.

    **note: `annotation` must be a instance of `type`.**
    '''
    if not isinstance(annotation, type):
        raise TypeError
    if not isinstance(param_type, ParamType):
        raise TypeError
    _PARAM_TYPE_MAP[annotation] = param_type

def get_param_type(annotation: type):
    '''
    try get registered `ParamType` by `annotation`,
    return `None` if not found.
    '''
    try:
        return _PARAM_TYPE_MAP[annotation]
    except (TypeError, KeyError): # unable to hash
        pass
