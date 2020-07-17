# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from click import echo
from click.testing import CliRunner
from click_anno import Injectable, command, inject

def test_injectable():
    class A(Injectable):
        @classmethod
        def __inject__(cls):
            return A()

    @command
    def func(a: A):
        assert isinstance(a, A)
        echo(f'{type(a).__name__}')

    result = CliRunner().invoke(func, [])
    assert result.output == "A\n"
    assert result.exit_code == 0


def test_inject():
    class Custom:
        pass

    inject(Custom, lambda: Custom())

    @command
    def func(a: Custom):
        assert isinstance(a, Custom)
        echo(f'{type(a).__name__}')

    result = CliRunner().invoke(func, [])
    assert result.output == "Custom\n"
    assert result.exit_code == 0
