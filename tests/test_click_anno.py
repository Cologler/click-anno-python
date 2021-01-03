# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import *

import click
from click.testing import CliRunner

from click_anno import click_app, command, anno

def test_anno():
    @click.command()
    @anno
    def touch(filename):
        click.echo(filename)

    result = CliRunner().invoke(touch, ['foo.txt'])
    assert result.exit_code == 0
    assert result.output == 'foo.txt\n'


def test_group():
    @click_app
    class App:
        def __init__(self, a, b):
            self._a = a
            self._b = b

        def method(self, e):
            click.echo(', '.join([self._a, self._b, e]))

    result = CliRunner().invoke(App, ['1', '2', 'method', '3'])
    assert result.exit_code == 0
    assert result.output == "1, 2, 3\n"

def test_group_custom():
    @click_app(command_name_format=lambda cmd, name: name.upper())
    class App:
        def __init__(self, a, b):
            self._a = a
            self._b = b

        def method(self, e):
            click.echo(', '.join([self._a, self._b, e]))

    result = CliRunner().invoke(App, ['1', '2', 'METHOD', '3'])
    assert result.exit_code == 0
    assert result.output == "1, 2, 3\n"

def test_multi_level_group():
    @click_app
    class App:
        def __init__(self, a):
            self._a = a

        class SubGroup:
            def __init__(self, b):
                self._b = b

            def method(self, e):
                click.echo(', '.join([self._b, e]))

    result = CliRunner().invoke(App, ['1', 'sub-group', '2', 'method', '3'])
    assert result.output == "2, 3\n"
    assert result.exit_code == 0

def test_click_app_not_inherit():
    class Base:
        def age(self):
            click.echo('age')

    @click_app
    class App(Base):
        pass

    result = CliRunner().invoke(App, ['age'])
    assert result.exit_code != 0

def test_click_app_allow_inherit():
    class Base:
        def age(self):
            click.echo('age')

    @click_app(allow_inherit=True)
    class App(Base):
        pass

    result = CliRunner().invoke(App, ['age'])
    assert result.output == "age\n"
    assert result.exit_code == 0

def test_default_in_argument():
    # by default, click does not allow show_default in click.argument
    # click_anno was overwrite it
    @command
    def func(a=10, *_):
        pass

    result = CliRunner().invoke(func, ['--help'])
    assert result.output.splitlines()[0] == "Usage: func [OPTIONS] [A=10]"
    assert result.exit_code == 0

def test_subcommand_name_should_remove_last_underline():
    @click_app
    class App:
        def import_(self):
            click.echo('imported')

    result = CliRunner().invoke(App, ['--help'])
    assert result.output.splitlines()[5:8] == ['Commands:', '  import']

    result = CliRunner().invoke(App, ['import'])
    assert result.output.splitlines()[0] == "imported"
    assert result.exit_code == 0
