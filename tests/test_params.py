# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import Tuple

import click
from click.testing import CliRunner

from click_anno import command

def test_non_arg():
    @command
    def func():
        click.echo('Hello World!')

    result = CliRunner().invoke(func, [])
    assert result.exit_code == 0
    assert result.output == 'Hello World!\n'

def test_one_required_args():
    @command
    def func(name):
        click.echo('Hello %s!' % name)

    result = CliRunner().invoke(func, ['Peter'])
    assert result.exit_code == 0
    assert result.output == 'Hello Peter!\n'

def test_one_required_typed_args_by_annotation():
    @command
    def func(count: int):
        assert isinstance(count, int)
        click.echo('Hello %s!' % count)

    result = CliRunner().invoke(func, ['1'])
    assert result.exit_code == 0
    assert result.output == 'Hello 1!\n'

def test_one_optional_typed_args_by_defval():
    @command
    def func(count=3):
        assert isinstance(count, int)
        click.echo('Hello %s!' % count)

    result_with_value = CliRunner().invoke(func, ['--count', '1'])
    assert result_with_value.exit_code == 0
    assert result_with_value.output == 'Hello 1!\n'

    result_without_value = CliRunner().invoke(func, [])
    assert result_without_value.exit_code == 0
    assert result_without_value.output == 'Hello 3!\n'

def test_multi_value_options():
    @command
    def func(pos1: float, pos2: float):
        assert isinstance(pos1, float)
        assert isinstance(pos2, float)
        click.echo('%s / %s' % (pos1, pos2))

    result = CliRunner().invoke(func, ['2.0', '3.0'])
    assert result.exit_code == 0
    assert result.output == '2.0 / 3.0\n'

def test_tuples_as_multi_value_options():
    @command
    def func(*, item: (str, int)):
        assert isinstance(item, tuple)
        assert isinstance(item[0], str)
        assert isinstance(item[1], int)
        click.echo('name=%s id=%d' % item)

    result = CliRunner().invoke(func, ['--item', 'peter', '1338'])
    assert result.exit_code == 0
    assert result.output == 'name=peter id=1338\n'

def test_var_args():
    @command
    def func(*args: tuple):
        assert isinstance(args, tuple)
        for item in args:
            assert isinstance(item, str)
        click.echo(f'args={args}')

    result = CliRunner().invoke(func, ['peter', '1338'])
    assert result.exit_code == 0
    assert result.output == "args=('peter', '1338')\n"

def test_var_args_generic():
    @command
    def func(*args: Tuple[int, ...]):
        assert isinstance(args, tuple)
        for item in args:
            assert isinstance(item, int)
        click.echo(f'args={args}')

    result = CliRunner().invoke(func, ['123', '456'])
    assert result.exit_code == 0
    assert result.output == "args=(123, 456)\n"

def test_inject_context():
    @command
    def func(a, ctx: click.Context):
        assert isinstance(ctx, click.Context)
        click.echo(f'args={a}')

    result = CliRunner().invoke(func, ['123'])
    assert result.exit_code == 0
    assert result.output == "args=123\n"

def test_all_type_args():
    @command
    def func(a, *b, c):
        click.echo(f'a={a}, b={b}, c={c}')

    result = CliRunner().invoke(func, ['A', 'B1', 'B2', '--c', 'C'])
    assert result.exit_code == 0
    assert result.output == "a=A, b=('B1', 'B2'), c=C\n"

def test_kwarg_name():
    @command
    def func(*, name_):
        click.echo('Hello %s!' % name_)

    result = CliRunner().invoke(func, ['--name', 'Peter'])
    assert result.exit_code == 0
    assert result.output == 'Hello Peter!\n'
