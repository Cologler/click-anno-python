# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from pytest import raises

from click_anno.core import ArgumentAdapter, ClickParameterBuilder
from click_anno.types import flag

def test_args():
    def func(name):
        pass

    param, = ArgumentAdapter.from_callable(func)
    builder: ClickParameterBuilder = param._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_ARGUMENT
    assert builder.decls == ['name']
    assert builder.attrs == {'required': True}

def test_args_with_anno_str():
    def func(name: str):
        pass

    param, = ArgumentAdapter.from_callable(func)
    builder: ClickParameterBuilder = param._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_ARGUMENT
    assert builder.decls == ['name']
    assert builder.attrs == {'required': True, 'type': str}

def test_args_with_anno_int():
    def func(name: int):
        pass

    param, = ArgumentAdapter.from_callable(func)
    builder: ClickParameterBuilder = param._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_ARGUMENT
    assert builder.decls == ['name']
    assert builder.attrs == {'required': True, 'type': int}

def test_args_with_default_str():
    def func(name='a'):
        pass

    param, = ArgumentAdapter.from_callable(func)
    builder: ClickParameterBuilder = param._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_OPTION
    assert builder.decls == ['--name', 'name']
    assert builder.attrs == {'default': 'a', 'show_default': True, 'type': str}

def test_var_args():
    def func(*args):
        pass

    param, = ArgumentAdapter.from_callable(func)
    builder: ClickParameterBuilder = param._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_ARGUMENT
    assert builder.decls == ['args']
    assert builder.attrs == {'nargs': -1}

def test_var_kwargs():
    def func(**kwargs):
        pass

    with raises(RuntimeError, match='click does not support dynamic'):
        ArgumentAdapter.from_callable(func)

def test_all_types_args_without_varpos():
    def func(a, b=1):
        pass

    params = ArgumentAdapter.from_callable(func)

    builder: ClickParameterBuilder = params[0]._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_ARGUMENT
    assert builder.decls == ['a']
    assert builder.attrs == {'required': True}

    builder: ClickParameterBuilder = params[1]._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_OPTION
    assert builder.decls == ['--b', 'b']
    assert builder.attrs == {'type': int, 'default': 1, 'show_default': True}

def test_all_types_args():
    def func(a, b=1, *c, d, e=2):
        pass

    params = ArgumentAdapter.from_callable(func)

    builder: ClickParameterBuilder = params[0]._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_ARGUMENT
    assert builder.decls == ['a']
    assert builder.attrs == {'required': True}

    builder: ClickParameterBuilder = params[1]._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_ARGUMENT
    assert builder.decls == ['b']
    assert builder.attrs == {'type': int, 'default': 1, 'show_default': True}

    builder: ClickParameterBuilder = params[2]._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_ARGUMENT
    assert builder.decls == ['c']
    assert builder.attrs == {'nargs': -1}

    builder: ClickParameterBuilder = params[3]._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_OPTION
    assert builder.decls == ['--d', 'd']
    assert builder.attrs == {'required': True}

    builder: ClickParameterBuilder = params[4]._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_OPTION
    assert builder.decls == ['--e', 'e']
    assert builder.attrs == {'type': int, 'default': 2, 'show_default': True}

def test_flag():
    def func(value: flag):
        pass

    param, = ArgumentAdapter.from_callable(func)
    builder: ClickParameterBuilder = param._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_OPTION
    assert builder.decls == ['--value', 'value']
    assert builder.attrs == {'is_flag': True, 'required': True}

def test_flag_with_default_false():
    def func(value: flag = False):
        pass

    param, = ArgumentAdapter.from_callable(func)
    builder: ClickParameterBuilder = param._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_OPTION
    assert builder.decls == ['--value', 'value']
    assert builder.attrs == {'is_flag': True, 'default': False, 'show_default': True}

def test_flag_with_default_true():
    def func(value: flag = True):
        pass

    param, = ArgumentAdapter.from_callable(func)
    builder: ClickParameterBuilder = param._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_OPTION
    assert builder.decls == ['--value', 'value']
    assert builder.attrs == {'is_flag': True, 'default': True, 'show_default': True}

def test_bool():
    def func(value: bool):
        pass

    param, = ArgumentAdapter.from_callable(func)
    builder: ClickParameterBuilder = param._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_OPTION
    assert builder.decls == ['--value/--no-value', 'value']
    assert builder.attrs == {'required': True}

def test_bool_default_false():
    def func(value: bool = False):
        pass

    param, = ArgumentAdapter.from_callable(func)
    builder: ClickParameterBuilder = param._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_OPTION
    assert builder.decls == ['--value/--no-value', 'value']
    assert builder.attrs == {'default': False, 'show_default': True}

def test_bool_default_true():
    def func(value: bool = True):
        pass

    param, = ArgumentAdapter.from_callable(func)
    builder: ClickParameterBuilder = param._builder
    assert builder.ptype == ClickParameterBuilder.TYPE_OPTION
    assert builder.decls == ['--value/--no-value', 'value']
    assert builder.attrs == {'default': True, 'show_default': True}
