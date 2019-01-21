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


def get_var_pos_param_type(parameter):
    if parameter.annotation is inspect.Parameter.empty:
        return str
    if parameter.annotation is tuple:
        return str
    if isinstance(parameter.annotation, typing._GenericAlias):
        if parameter.annotation.__origin__ is tuple:
            args = parameter.annotation.__args__
            if len(args) == 2 and args[1] is Ellipsis:
                return args[0]
    raise ValueError(f'annotation of parameter {parameter.name} must be tuple or typing.Tuple[?, ...]')


class ArgumentAdapter:
    def __init__(self, parameter):
        self._parameter = parameter
        self._parameter_key = parameter.name.strip('_')
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

        if parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
            if parameter.annotation is not inspect.Parameter.empty:
                if parameter.annotation is tuple:
                    self._click_decorator_attrs.setdefault('nargs', -1)

        elif parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            self._click_decorator_attrs.setdefault('nargs', -1)

        elif parameter.kind is inspect.Parameter.KEYWORD_ONLY:
            self._click_decorator_name = 'option'
            self._click_decorator_attrs['required'] = True

        elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
            pass

        else:
            raise NotImplementedError

        if parameter.annotation is not inspect.Parameter.empty:
            if parameter.annotation is tuple:
                self._click_decorator_attrs.setdefault('nargs', -1)
            elif isinstance(parameter.annotation, typing._GenericAlias):
                if parameter.annotation.__origin__ is tuple:
                    args = parameter.annotation.__args__
                    if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
                        if len(args) == 2 and args[1] is Ellipsis:
                            self._click_decorator_attrs['type'] = args[0]
                        else:
                            raise ValueError(\
                                f'annotation of parameter {parameter.name} must be tuple or typing.Tuple[?, ...]')
                    else:
                        if any(x is not args[0] for x in args):
                            raise ValueError(\
                                f'annotation of parameter {parameter.name} must be same types')
                        else:
                            self._click_decorator_attrs.setdefault('nargs', len(args))
                            self._click_decorator_attrs['type'] = args[0]
                else:
                    raise ValueError('generic type must be typing.Tuple')
            else:
                self._click_decorator_attrs.setdefault('type', parameter.annotation)

        if self._click_decorator_name is None:
            if parameter.default is inspect.Parameter.empty:
                self._click_decorator_name = 'argument'
            else:
                self._click_decorator_name = 'option'

        if parameter.default is not inspect.Parameter.empty:
            self._click_decorator_attrs.setdefault('type', type(parameter.default))
            self._click_decorator_attrs['default'] = parameter.default
            self._click_decorator_attrs['show_default'] = True

        if self._click_decorator_name == 'option':
            self._click_decorator_decls.append('--' + self._parameter_key.replace('_', '-'))
        self._click_decorator_decls.append(self._parameter_key)

        assert self._click_decorator_name in ('argument', 'option')

    def get_click_decorator(self):
        if self._click_decorator_name:
            decorator =  getattr(click, self._click_decorator_name)
            return decorator(*self._click_decorator_decls, **self._click_decorator_attrs)

    def convert(self, args, kwargs, to_args: list, to_kwargs: dict):
        assert not args
        if self._injector:
            val = self._injector.get_value()
        else:
            val = kwargs.pop(self._parameter_key)
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
    