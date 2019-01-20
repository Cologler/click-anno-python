# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import inspect
import typing

import click


from .injectors import Injector, inject


class ArgumentAdapter:
    def __init__(self, parameter):
        self._parameter = parameter
        self._click_decorator_name: str = None
        self._click_decorator_decls: list = []
        self._click_decorator_attrs: dict = {}
        self._injector: Injector = None

        if isinstance(parameter.annotation, Injector):
            self._injector = parameter.annotation
        else:
            self._init_click_attrs()

    def _init_click_attrs(self):
        parameter = self._parameter

        self._click_decorator_decls: list = []
        self._click_decorator_attrs: dict = {}

        if parameter.annotation is not inspect.Parameter.empty:
            if isinstance(parameter.annotation, typing._GenericAlias):
                if parameter.annotation.__origin__ is tuple:
                    self._click_decorator_attrs['type'] = parameter.annotation.__args__
                else:
                    raise NotImplementedError

            else:
                self._click_decorator_attrs['type'] = parameter.annotation

        if parameter.default is inspect.Parameter.empty:
            self._click_decorator_name = 'argument'
        else:
            self._click_decorator_name = 'option'
            self._click_decorator_attrs['type'] = type(parameter.default)
            self._click_decorator_attrs['default'] = parameter.default
            self._click_decorator_attrs['show_default'] = True

        if parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
            pass

        elif parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            self._click_decorator_attrs.setdefault('nargs', -1)
            if 'type' in self._click_decorator_attrs:
                argtype = self._click_decorator_attrs['type']
                assert isinstance(argtype, tuple) and len(argtype) == 1
                self._click_decorator_attrs['type'] = argtype[0]

        elif parameter.kind is inspect.Parameter.KEYWORD_ONLY:
            self._click_decorator_name = 'option'
            self._click_decorator_attrs['required'] = True

        elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
            pass

        else:
            raise NotImplementedError

        if self._click_decorator_name == 'option':
            self._click_decorator_decls.append('--' + parameter.name.replace('_', '-'))
        else:
            assert self._click_decorator_name == 'argument'
        self._click_decorator_decls.append(parameter.name)

    def get_click_decorator(self):
        if self._click_decorator_name:
            decorator =  getattr(click, self._click_decorator_name)
            return decorator(*self._click_decorator_decls, **self._click_decorator_attrs)

    def convert(self, args, kwargs, to_args: list, to_kwargs: dict):
        assert not args
        if self._injector:
            val = self._injector.get_value()
        else:
            val = kwargs.pop(self._parameter.name)
        if self._parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            to_args.extend(val)
        else:
            to_kwargs[self._parameter.name] = val


class CallableAdapter:
    def __init__(self, func):
        self._func = func
        sign = inspect.signature(func)
        self._args_adapters = [ArgumentAdapter(param) for param in sign.parameters.values()]

        # clone func info
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __call__(self, *args, **kwargs):
        to_args = []
        to_kwargs = {}
        for adapter in self._args_adapters:
            adapter.convert(args, kwargs, to_args, to_kwargs)
        return self._func(*to_args, **to_kwargs)

    def create_command(self):
        func = self
        for adapter in reversed(self._args_adapters):
            decorator = adapter.get_click_decorator()
            if decorator:
                func = decorator(func)
        return click.command()(func)


def command(func):
    return CallableAdapter(func).create_command()
    sign = inspect.signature(func)
    args_adapters = []
    for param in reversed(sign.parameters.values()):
        adapter = ArgumentAdapter(param)
        args_adapters.append(adapter)
        decorator =  getattr(click, adapter.click_decorator_name)
        func = decorator(*adapter.click_decorator_decls, **adapter.click_decorator_attrs)(func)
    return click.command()(func)
