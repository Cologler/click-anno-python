# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import abc

import click

class Injector:
    @abc.abstractmethod
    def get_value(self):
        return click.get_current_context()


class ClickContextInjector(Injector):
    def get_value(self):
        return click.get_current_context()


def inject(type):
    if type is click.Context:
        return ClickContextInjector()
    raise NotImplementedError
