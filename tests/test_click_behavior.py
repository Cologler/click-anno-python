# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from pytest import raises

import click

def test_click_did_not_allow_show_default_in_arguments():
    with raises(TypeError, match="got an unexpected keyword argument 'show_default'"):
        @click.argument(show_default=True)
        def func():
            pass
