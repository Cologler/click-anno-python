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


class ObjectInjector(Injector):
    def __init__(self, object_type):
        self._object_type = object_type

    def get_value(self):
        return click.get_current_context().find_object(self._object_type)


def inject(type):
    if type is click.Context:
        return ClickContextInjector()
    else:
        return ObjectInjector(type)
