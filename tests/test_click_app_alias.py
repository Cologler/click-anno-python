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
            'abc\ncde'
            pass

        first_name = name

    result = CliRunner().invoke(App, ['--help'])
    lines = result.output.splitlines()[-2:]
    assert lines == [
        'Commands:',
        '  name  abc cde (alias: first-name)'
    ]
    assert result.exit_code == 0

    result = CliRunner().invoke(App, ['name', '--help'])
    lines = result.output.splitlines()[1:4]
    assert lines == [
        '',
        '  abc cde  (alias: first-name)',
        ''
    ]
    assert result.exit_code == 0

    result = CliRunner().invoke(App, ['first-name', '--help'])
    lines = result.output.splitlines()[1:4]
    assert lines == [
        '',
        '  abc cde  (alias of: name)',
        ''
    ]
    assert result.exit_code == 0
