# -*- coding: utf-8 -*-
#
# Copyright (c) 2021~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import click
from click.testing import CliRunner

from click_anno import command

def test_args_positional_optional():
    @command
    def func(name='Guest', /):
        click.echo('Hello %s!' % name)

    result = CliRunner().invoke(func, ['Peter'])
    assert result.exit_code == 0
    assert result.output == 'Hello Peter!\n'

    result = CliRunner().invoke(func, [])
    assert result.exit_code == 0
    assert result.output == 'Hello Guest!\n'
