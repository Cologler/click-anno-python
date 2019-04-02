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


class FindObjectInjector(Injector):
    def __init__(self, object_type):
        self._object_type = object_type

    def get_value(self):
        return click.get_current_context().find_object(self._object_type)


def find(object_type: type):
    '''
    inject object from `Click.Context.find_object()`
    '''
    return FindObjectInjector(object_type)


class EnsureObjectInjector(Injector):
    def __init__(self, object_type):
        self._object_type = object_type

    def get_value(self):
        return click.get_current_context().ensure_object(self._object_type)


def ensure(object_type: type):
    '''
    inject object from `Click.Context.ensure_object()`
    '''
    return EnsureObjectInjector(object_type)


TYPE_INJECTOR_MAP = {
    click.Context: ClickContextInjector()
}
