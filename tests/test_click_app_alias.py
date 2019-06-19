# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import click
from click.testing import CliRunner

from click_anno import click_app

def test_alias():
    @click_app
    class App:
        def name(self, x):
            click.echo(x)

        alias = name

    result = CliRunner().invoke(App, ['name', 'val'])
    assert result.output == "val\n"
    assert result.exit_code == 0

    result = CliRunner().invoke(App, ['alias', 'val'])
    assert result.output == "val\n"
    assert result.exit_code == 0

def test_alias_help():
    @click_app
    class App:
        def name(self, x):
            'abc'
            pass

        alias = name

    result = CliRunner().invoke(App, ['--help'])
    lines = result.output.splitlines()[-3:]
    assert lines == [
        'Commands:',
        '  alias  alias of command (name)',
        '  name   abc'
    ]
    assert result.exit_code == 0
