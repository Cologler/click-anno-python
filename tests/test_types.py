# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import click
from click.testing import CliRunner

from click_anno import command

def test_flag():
    from click_anno.types import flag

    @command
    def func(is_ok: flag):
        click.echo(f'{is_ok!r}')

    result = CliRunner().invoke(func, [])
    assert result.exit_code == 0
    assert result.output == 'False\n'

    result = CliRunner().invoke(func, ['--is-ok'])
    assert result.exit_code == 0
    assert result.output == 'True\n'

def test_flag_with_default_false():
    from click_anno.types import flag

    @command
    def func(is_ok: flag = False):
        click.echo(f'{is_ok!r}')

    result = CliRunner().invoke(func, [])
    assert result.exit_code == 0
    assert result.output == 'False\n'

    result = CliRunner().invoke(func, ['--is-ok'])
    assert result.exit_code == 0
    assert result.output == 'True\n'

def test_flag_with_default_true():
    from click_anno.types import flag

    @command
    def func(is_ok: flag = True):
        click.echo(f'{is_ok!r}')

    result = CliRunner().invoke(func, [])
    assert result.exit_code == 0
    assert result.output == 'True\n'

    result = CliRunner().invoke(func, ['--is-ok'])
    assert result.exit_code == 0
    assert result.output == 'False\n'

def test_enum():
    from enum import Enum, auto

    class Kind(Enum):
        a = auto()
        b = auto()
        c_d = auto()

    @command
    def func(kind: Kind):
        assert isinstance(kind, Kind)
        click.echo(f'{kind.name}')

    result = CliRunner().invoke(func, ['a'])
    assert result.exit_code == 0
    assert result.output == 'a\n'

    result = CliRunner().invoke(func, ['c-d'])
    assert result.exit_code == 0
    assert result.output == 'c_d\n'

def test_enum_with_default():
    from enum import Enum, auto

    class Kind(Enum):
        a = auto()
        b = auto()
        c_d = auto()

    @command
    def func(kind: Kind = Kind.a):
        assert isinstance(kind, Kind)
        click.echo(f'{kind.name}')

    result = CliRunner().invoke(func, [])
    assert result.exit_code == 0
    assert result.output == 'a\n'

    result = CliRunner().invoke(func, ['--kind', 'b'])
    assert result.exit_code == 0
    assert result.output == 'b\n'

def test_bool():
    @command
    def func(is_ok: bool):
        click.echo(f'{is_ok!r}')

    result = CliRunner().invoke(func, [])
    assert result.exit_code == 0
    assert result.output == 'False\n'

    result = CliRunner().invoke(func, ['--is-ok'])
    assert result.exit_code == 0
    assert result.output == 'True\n'

    result = CliRunner().invoke(func, ['--no-is-ok'])
    assert result.exit_code == 0
    assert result.output == 'False\n'

def test_bool_default_false():
    @command
    def func(is_ok: bool = False):
        click.echo(f'{is_ok!r}')

    result = CliRunner().invoke(func, [])
    assert result.exit_code == 0
    assert result.output == 'False\n'

    result = CliRunner().invoke(func, ['--is-ok'])
    assert result.exit_code == 0
    assert result.output == 'True\n'

    result = CliRunner().invoke(func, ['--no-is-ok'])
    assert result.exit_code == 0
    assert result.output == 'False\n'

def test_bool_default_true():
    @command
    def func(is_ok: bool = True):
        click.echo(f'{is_ok!r}')

    result = CliRunner().invoke(func, [])
    assert result.exit_code == 0
    assert result.output == 'True\n'

    result = CliRunner().invoke(func, ['--is-ok'])
    assert result.exit_code == 0
    assert result.output == 'True\n'

    result = CliRunner().invoke(func, ['--no-is-ok'])
    assert result.exit_code == 0
    assert result.output == 'False\n'

def test_register_param_type():
    from click_anno.types import register_param_type

    class ClassA:
        value = None

    class ClassAParamType(click.ParamType):
        def convert(self, value, param, ctx):
            ca = ClassA()
            ca.value = value
            return ca

    register_param_type(ClassA, ClassAParamType())

    @command
    def func(c: ClassA):
        click.echo(f'{c.value!r}')

    result = CliRunner().invoke(func, ['abc'])
    assert result.exit_code == 0
    assert result.output == "'abc'\n"
