# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import abc

import click

class Injector(abc.ABC):
    @abc.abstractmethod
    def get_value(self):
        raise NotImplementedError


class _CallableInjector(Injector):
    def __init__(self, factory):
        super().__init__()
        self._factory = factory

    def get_value(self):
        return self._factory()


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


class Injectable(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def __inject__(cls):
        raise NotImplementedError


class _InjectableInjector(Injector):
    def __init__(self, injectable_type):
        self._injectable_type = injectable_type

    def get_value(self):
        return self._injectable_type.__inject__()

_INJECTOR_MAPS = {}

def inject(annotation: type, factory):
    '''
    mark a type should be auto inject by call `factory` instead of parse from command line.
    '''
    if not callable(factory):
        raise TypeError
    _INJECTOR_MAPS[annotation] = _CallableInjector(factory)


def get_injector(annotation: type):
    if isinstance(annotation, Injector):
        return annotation

    try:
        return _INJECTOR_MAPS[annotation]
    except (KeyError, ValueError):
        pass

    if isinstance(annotation, type) and issubclass(annotation, Injectable):
        return _InjectableInjector(annotation)


inject(click.Context, lambda: click.get_current_context())
