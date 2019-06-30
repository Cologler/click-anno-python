# -*- coding: utf-8 -*-
#
# Copyright (c) 2019~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import inspect
import typing
import functools
import itertools

import click

from .injectors import Injector, get_injector
from .snake_case import convert as sc_convert
from .types import flag, Enum, _EnumChoice

_KEY_ATTRS = '__click_anno_attrs'

def attrs(**kwargs):
    '''
    append attrs to command or group like:

    ``` py
    @click_app
    @attrs(...)
    class ...
    ```

    attrs will pass into `click` module.
    '''
    def wrapper(type_or_func):
        setattr(type_or_func, _KEY_ATTRS, dict(kwargs))
        return type_or_func
    return wrapper


class _Argument(click.Argument):
    __slots__ = ('show_default')

    def __init__(self, *args, **kwargs):
        self.show_default = kwargs.pop('show_default', False)
        super().__init__(*args, **kwargs)

    def make_metavar(self):
        var: str = super().make_metavar()
        if self.show_default:
            if var.startswith('[') and var.endswith(']'):
                var = var[1:-1]
                var = '[%s=%s]' % (var, self.default)
        return var


class ClickParameterBuilder:
    __slots__ = ('ptype', 'decls', 'attrs')

    TYPE_ARGUMENT = 'argument'
    TYPE_OPTION = 'option'
    TYPES = (TYPE_ARGUMENT, TYPE_OPTION)

    def __init__(self):
        self.ptype: str = None # click parameter type
        self.decls = []
        self.attrs = {}

    def get_decorator(self):
        assert self.ptype in self.TYPES

        attrs = self.attrs.copy()
        decls = self.decls.copy()
        if self.ptype == self.TYPE_ARGUMENT:
            attrs['cls'] = _Argument
        decorator =  getattr(click, self.ptype)
        return decorator(*decls, **attrs)

    def set_nargs(self, value: int):
        '''set nargs, -1 for var len.'''
        assert self.ptype is not None
        try:
            assert self.attrs['nargs'] == value
        except KeyError:
            self.attrs['nargs'] = value

    def set_flag(self):
        self.attrs['is_flag'] = True

    def set_default(self, value):
        assert self.ptype is not None

        if self.attrs.get('is_flag', False):
            # click is unable to parse flag as bool
            # so keep it has no type.
            pass
        elif value is not None:
            self.attrs.setdefault('type', type(value))

        self.attrs['default'] = value

        # show_default only work on option
        # so I make a subclass for argument
        self.attrs['show_default'] = True

    def set_name(self, name: str):
        assert self.ptype is not None

        name = name.strip('_')
        cname = name.replace('_', '-')

        if self.ptype == self.TYPE_OPTION:
            if self.attrs.get('type') is bool:
                # if not del `type`, will raise:
                # TypeError: Got secondary option for non boolean flag.
                del self.attrs['type']
                self.decls.append(f'--{cname}/--no-{cname}')
            else:
                self.decls.append('--' + cname)

        self.decls.append(name)


_UNSET = object()


class ArgumentAdapter:
    @classmethod
    def from_parameter(cls, param: inspect.Parameter, kind=None):
        default = _UNSET if param.default is inspect.Parameter.empty else param.default
        annotation = _UNSET if param.annotation is inspect.Parameter.empty else param.annotation
        if kind is None:
            kind = param.kind
        adapter = cls(param.name, kind, default, annotation)
        return adapter

    @classmethod
    def from_callable(cls, func) -> list:
        sign = inspect.signature(func)

        # if contains var pos args
        # all before it should be TYPE_ARGUMENT
        param_kinds = [z.kind for z in sign.parameters.values()]
        try:
            index = param_kinds.index(inspect.Parameter.VAR_POSITIONAL)
        except ValueError:
            index = 0
        while index:
            index -= 1
            param_kinds[index] = inspect.Parameter.POSITIONAL_ONLY

        adapters = []
        for p, k in zip(sign.parameters.values(), param_kinds):
            if p.name == '_': # ignore param which named `_`
                continue
            adapters.append(cls.from_parameter(p, k))

        return adapters

    def __init__(self, param_name: str, param_kind: inspect._ParameterKind, param_def, param_anno):
        if param_kind is inspect.Parameter.VAR_KEYWORD:
            raise RuntimeError('click does not support dynamic options.')

        self._parameter_name: str = param_name # this name use for pass to the function
        self._parameter_key: str = param_name.strip('_') # this key use for get value from click args
        self._parameter_annotation = param_anno
        self._parameter_kind: inspect._ParameterKind = param_kind
        self._parameter_default = param_def

        self._injector: Injector = get_injector(self._parameter_annotation)
        self._builder: ClickParameterBuilder = None

        if not self._injector:
            self._builder = ClickParameterBuilder()
            self._init_click_attrs()

    def _init_click_attrs(self):
        kind = self._parameter_kind
        annotation = self._parameter_annotation
        default = self._parameter_default

        if kind is inspect.Parameter.POSITIONAL_ONLY:
            self._builder.ptype = ClickParameterBuilder.TYPE_ARGUMENT
        elif kind is inspect.Parameter.KEYWORD_ONLY:
            self._builder.ptype = ClickParameterBuilder.TYPE_OPTION
        elif annotation in (flag, bool):
            self._builder.ptype = ClickParameterBuilder.TYPE_OPTION
        elif default is _UNSET:
            self._builder.ptype = ClickParameterBuilder.TYPE_ARGUMENT
        else:
            self._builder.ptype = ClickParameterBuilder.TYPE_OPTION

        if kind is inspect.Parameter.VAR_POSITIONAL:
            self._builder.set_nargs(-1)

        self._init_click_type()

        if default is _UNSET:
            if kind is not inspect.Parameter.VAR_POSITIONAL:
                self._builder.attrs['required'] = True
        else:
            self._builder.set_default(default)

        self._builder.set_name(self._parameter_key)

    def _init_click_type(self):
        kind = self._parameter_kind
        annotation = self._parameter_annotation

        if annotation is _UNSET:
            return

        elif annotation is tuple:
            return self._builder.set_nargs(-1)

        elif annotation is flag:
            return self._builder.set_flag()

        elif isinstance(annotation, type):
            if issubclass(annotation, Enum):
                self._builder.attrs['type'] = _EnumChoice(annotation)

        elif isinstance(annotation, typing._GenericAlias):
            # for `Tuple[?]`
            if annotation.__origin__ is tuple:
                args = annotation.__args__
                if kind is inspect.Parameter.VAR_POSITIONAL:
                    assert self._builder.attrs['nargs'] == -1
                    if len(args) == 2 and args[1] is Ellipsis:
                        self._builder.attrs['type'] = args[0]
                    else:
                        raise ValueError(\
                            f'anno of param {self._parameter_name} must be tuple or typing.Tuple[?, ...]')
                else:
                    if any(x is not args[0] for x in args):
                        raise ValueError(\
                            f'anno of param {self._parameter_name} must be same types')
                    else:
                        self._builder.set_nargs(len(args))
                        self._builder.attrs['type'] = args[0]
            else:
                raise ValueError('generic type must be typing.Tuple')

        self._builder.attrs.setdefault('type', annotation)

    def get_click_decorator(self):
        if self._builder:
            return self._builder.get_decorator()

    def convert(self, args, kwargs, to_args: list, to_kwargs: dict):
        assert not args

        if self._injector:
            val = self._injector.get_value()
        else:
            val = kwargs.pop(self._parameter_key)

        assert self._parameter_kind is not inspect.Parameter.VAR_KEYWORD

        if self._parameter_kind is inspect.Parameter.KEYWORD_ONLY:
            to_kwargs[self._parameter_name] = val
        elif self._parameter_kind is inspect.Parameter.VAR_POSITIONAL:
            to_args.extend(val)
        else:
            to_args.append(val)


class CallableAdapter:
    @classmethod
    def from_func(cls, func):
        adapter = cls(func)
        adapter.args_adapters.extend(ArgumentAdapter.from_callable(func))
        return adapter

    def __init__(self, func):
        self._func = func
        self.args_adapters = []

        # clone func info
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __call__(self, *args, **kwargs):
        to_args = []
        to_kwargs = {}
        for adapter in self.args_adapters:
            adapter.convert(args, kwargs, to_args, to_kwargs)
        return self._func(*to_args, **to_kwargs)

    def get_wrapped_func(self):
        func = self
        for adapter in reversed(self.args_adapters):
            decorator = adapter.get_click_decorator()
            if decorator:
                func = decorator(func)
        return func


def command(func) -> click.Command:
    '''
    build a `function` as a `click.Command`.
    '''
    wrapped_func = CallableAdapter.from_func(func).get_wrapped_func()
    attrs = getattr(func, _KEY_ATTRS, {})
    return click.command(**attrs)(wrapped_func)


def create_init_wrapper(cls):
    @functools.wraps(cls)
    def init_wrapper(*args, **kwargs):
        ctx = click.get_current_context()
        ctx.__instance = cls(*args, **kwargs)
    return init_wrapper

def create_method_wrapper(func):
    @functools.wraps(func)
    def method_wrapper(*args, **kwargs):
        ctx = click.get_current_context()
        instance = ctx.parent.__instance
        return func(instance, *args, **kwargs)
    return method_wrapper


class GroupBuilderOptions:
    allow_inherit = False

    def group_name_format(self, command, name):
        return sc_convert(name).replace('_', '-')

    def command_name_format(self, command, name):
        return name.lower().replace('_', '-')


def _iter_subcommands_not_inherit(cls):
    for name, sub_cmd in vars(cls).items():
        if name[:1] != '_':
            yield name, sub_cmd

def _iter_subcommands_allow_inherit(cls):
    for name in dir(cls):
        if name[:1] != '_':
            yield name, getattr(cls, name)

class _SubCommandBuilder:
    def __init__(self, is_group: bool, command, name: str, options: GroupBuilderOptions):
        self.is_group = is_group
        self.command = command
        self.name = name
        self.attrs: dict = getattr(command, _KEY_ATTRS, {}).copy()
        self.options = options
        self.attrs.setdefault('help', str(command.__doc__))

    def update_name(self, is_default):
        if self.is_group:
            format_func = self.options.group_name_format
        else:
            format_func = self.options.command_name_format
        formated_name = format_func(self.command, self.name)
        if is_default:
            self.attrs.setdefault('name', formated_name)
        else:
            # alias should not use name from `attrs`, so we overwrite it.
            self.attrs['name'] = formated_name


def click_app(cls: type = None, **kwargs) -> click.Group:
    '''
    build a `class` as a `click.Group`.

    use `kwargs` to override members of `GroupBuilderOptions`.
    '''
    options = GroupBuilderOptions()
    vars(options).update(kwargs)

    def make_group(cls: type, group: click.Group, attrs: dict):
        'make group from a class'
        adapter = CallableAdapter(create_init_wrapper(cls))
        adapter.args_adapters.extend(ArgumentAdapter.from_callable(cls))
        group = group.group(**attrs)(adapter.get_wrapped_func())

        if options.allow_inherit:
            iter_subcommands = _iter_subcommands_allow_inherit(cls)
        else:
            iter_subcommands = _iter_subcommands_not_inherit(cls)

        # list subcommands
        subcmdinfo_map = {}
        for name, subcommand in iter_subcommands:
            if callable(subcommand):
                subcmdinfo = _SubCommandBuilder(
                    is_group=isinstance(subcommand, type),
                    command=subcommand,
                    name=name,
                    options=options
                )
                subcmdinfo_map.setdefault(subcommand, []).append(subcmdinfo)

        # prepare subcommands attrs
        for attrs_info_list in subcmdinfo_map.values():
            for index, subcmdinfo in enumerate(attrs_info_list):
                subcmdinfo: _SubCommandBuilder
                subcmdinfo.update_name(index == 0)
            names = [z.attrs['name'] for z in attrs_info_list]
            if len(attrs_info_list) > 1:
                attrs_info_list[0].attrs['help'] += f'\n (alias: {", ".join(names[1:])})'
                for subcmdinfo in attrs_info_list[1:]:
                    subcmdinfo: _SubCommandBuilder
                    sub_attrs = subcmdinfo.attrs
                    # hide alias
                    sub_attrs['hidden'] = True
                    sub_attrs['help'] += f'\n (alias of: {names[0]})'

        # add subcommands into group
        for subcmdinfo in itertools.chain(*subcmdinfo_map.values()):
            subcmdinfo: _SubCommandBuilder
            if subcmdinfo.is_group:
                make_group(subcmdinfo.command, group, subcmdinfo.attrs)
            else:
                adapter = CallableAdapter(create_method_wrapper(subcmdinfo.command))
                adapter.args_adapters.extend(ArgumentAdapter.from_callable(subcmdinfo.command))
                adapter.args_adapters.pop(0) # remove arg `self`
                group.command(**subcmdinfo.attrs)(adapter.get_wrapped_func())

        return group

    def warpper(cls) -> click.Group:
        attrs: dict = getattr(cls, _KEY_ATTRS, {}).copy()
        attrs.setdefault('name', options.group_name_format(cls, cls.__name__))
        return make_group(cls, click, attrs)

    return warpper(cls) if cls else warpper
