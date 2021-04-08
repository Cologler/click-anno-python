# -*- coding: utf-8 -*-
#
# Copyright (c) 2021~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

_KEY_ATTRS = '__click_anno_attrs__'

def attrs(**kwargs):
    '''
    append attrs to command or group like:

    ``` py
    @click_app
    @attrs(...)
    class ...
    ```

    attrs will pass into `click` via `click.command(**attrs)(...)`.
    '''
    def wrapper(type_or_func):
        attrs: dict = get_attrs(type_or_func, False)
        attrs.update(kwargs)
        setattr(type_or_func, _KEY_ATTRS, attrs)
        return type_or_func
    return wrapper


def get_attrs(target, clone=True):
    attrs = getattr(target, _KEY_ATTRS, {})
    return attrs.copy() if clone else attrs
