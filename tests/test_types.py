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
