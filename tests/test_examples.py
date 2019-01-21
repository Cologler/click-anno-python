# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import Tuple

import click
from click.testing import CliRunner

from click_anno import command, inject

def test_basic_arguments():
    @command
    def touch(filename):
        click.echo(filename)

    result = CliRunner().invoke(touch, ['foo.txt'])
    assert result.exit_code == 0
    assert result.output == 'foo.txt\n'

def test_variadic_arguments():
    @command
    def copy(src: tuple, dst):
        for fn in src:
            click.echo('move %s to folder %s' % (fn, dst))

    result = CliRunner().invoke(copy, ['foo.txt', 'bar.txt', 'my_folder'])
    assert result.exit_code == 0
    assert result.output == 'move foo.txt to folder my_folder\nmove bar.txt to folder my_folder\n'

def test_basic_value_options():
    @command
    def dots(n=1):
        click.echo('.' * n)

    result = CliRunner().invoke(dots, [])
    assert result.exit_code == 0
    assert result.output == '.\n'

    result_5 = CliRunner().invoke(dots, ['--n', '5'])
    assert result_5.exit_code == 0
    assert result_5.output == '.....\n'

def test_required_value_options():
    @command
    def dots(*, n: int):
        click.echo('.' * n)

    result = CliRunner().invoke(dots, ['--n=2'])
    assert result.exit_code == 0
    assert result.output == '..\n'

def test_multi_value_options():
    @command
    def findme(*, pos: Tuple[float, float]):
        click.echo('%s / %s' % pos)

    result = CliRunner().invoke(findme, ['--pos', '2.0', '3.0'])
    assert result.exit_code == 0
    assert result.output == '2.0 / 3.0\n'

def test_tuples_as_multi_value_options():
    @command
    def putitem(*, item: (str, int)):
        click.echo('name=%s id=%d' % item)

    result = CliRunner().invoke(putitem, ['--item', 'peter', '1338'])
    assert result.exit_code == 0
    assert result.output == 'name=peter id=1338\n'
