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
