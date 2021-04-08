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
import click.utils

from .injectors import Injector, get_injector
from .snake_case import convert as sc_convert
from .types import flag, Enum, _EnumChoice, get_param_type
from .utils import get_attrs


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
            param_type = get_param_type(annotation)
            if param_type is not None:
                self._builder.attrs['type'] = param_type
            elif issubclass(annotation, Enum):
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


def anno(func=None) -> typing.Callable:
    '''
    convert all annotations as click decorators to decorate the `func`,
    return the decorated function.

    you need to manually decorate `click.command(...)` or `click.group(...)` on the returned function.

    this also ignore all attrs that add via `click_anno.attrs`.

    example:

    ``` py
    @click.command()
    @anno
    def act():
        ...
    ```
    '''

    def wrapper(func):
        return CallableAdapter.from_func(func).get_wrapped_func()

    return wrapper(func) if func else wrapper


def command(func) -> click.Command:
    '''
    build a `function` as a `click.Command`.
    '''
    wrapped_func = anno(func)
    attrs = get_attrs(func, False)
    return click.command(**attrs)(wrapped_func)


def _create_init_wrapper(cls):
    @functools.wraps(cls)
    def init_wrapper(*args, **kwargs):
        ctx = click.get_current_context()
        ctx.__instance = cls(*args, **kwargs)
    return init_wrapper

def _create_method_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ctx = click.get_current_context()
        instance = ctx.parent.__instance
        return func(instance, *args, **kwargs)
    return wrapper


class GroupBuilderOptions:
    allow_inherit = False

    @staticmethod
    def _remove_underline_suffix(name: str):
        if not name.startswith('_') and name.endswith('_'):
            # user may want add a sub command `import`,
            # but `import` is a keyword in python,
            # so user use `import_` as command.
            # here we remove the last '_'.
            # if user still want the '_' suffix, try use `import__`.
            if len(name) > 1:
                return name[:-1]
        return name

    def group_name_format(self, command, name: str) -> str:
        name = self._remove_underline_suffix(name)
        return sc_convert(name).replace('_', '-')

    def command_name_format(self, command, name: str) -> str:
        name = self._remove_underline_suffix(name)
        return name.lower().replace('_', '-')

    def is_group(self, command) -> bool:
        '''
        check if the command is a group or not.

        by default, only the sub class is a group.
        '''
        return isinstance(command, type) or isinstance(command, click.MultiCommand)

    def name_format(self, is_group: bool, command, name: str) -> str:
        'format name by `command` and `name`'
        if is_group:
            return self.group_name_format(command, name)
        else:
            return self.command_name_format(command, name)

    def find_origin_name(self, command, names: typing.List[str]) -> str:
        '''
        find origin name so we known which is alias, which is not;
        the origin name must in `names`.

        NOTE: the item of names is *NOT* the formated name.
        '''
        assert names
        name = command.__name__
        if name in names:
            return name
        return names[0] # all are alias, return the first one.

    def iter_subcommands_not_inherit(self, cls):
        for name, sub_cmd in vars(cls).items():
            if name[:1] != '_':
                yield name, sub_cmd

    def iter_subcommands_allow_inherit(self, cls):
        for name in dir(cls):
            if name[:1] != '_':
                yield name, getattr(cls, name)

    def iter_subcommands(self, cls):
        if self.allow_inherit:
            return self.iter_subcommands_allow_inherit(cls)
        else:
            return self.iter_subcommands_not_inherit(cls)


class _SubCommandBuilder:
    def __init__(self, is_group: bool, command, name: str, formated_name: str):
        self.is_group = is_group
        self.command = command
        self.name = name
        self.attrs: dict = get_attrs(command)
        self.formated_name = formated_name

        # set only if user use default value
        self.attrs.setdefault('help', str(command.__doc__ or ''))
        self.attrs.setdefault('name', self.formated_name)

    def update_name(self, is_default):
        'update name to `attrs`'
        if is_default:
            self.attrs.setdefault('name', self.formated_name)
        else:
            # alias should not use name from `attrs`, so we overwrite it.
            self.attrs['name'] = self.formated_name


def click_app(cls: type = None, **kwargs) -> click.Group:
    '''
    build a `class` as a `click.Group`.

    use `kwargs` to override members of `GroupBuilderOptions`.
    '''
    options = GroupBuilderOptions()
    vars(options).update(kwargs)

    def make_group(cls: type, attrs: dict):
        'make group from a class'
        adapter = CallableAdapter(_create_init_wrapper(cls))
        adapter.args_adapters.extend(ArgumentAdapter.from_callable(cls))
        group = click.group(**attrs)(adapter.get_wrapped_func())

        # list subcommands
        user_commands = []
        map_by_cmd = {}
        for name, subcommand in list(options.iter_subcommands(cls)):
            is_group = options.is_group(subcommand)
            formated_name = options.name_format(is_group, subcommand, name)

            if isinstance(subcommand, click.BaseCommand):
                user_commands.append((subcommand, formated_name))

            elif callable(subcommand):
                builder = _SubCommandBuilder(
                    is_group=is_group,
                    command=subcommand,
                    name=name,
                    formated_name=formated_name
                )
                user_commands.append(builder)
                # group by callable so we can detect alias
                map_by_cmd.setdefault(subcommand, []).append(builder)

        # prepare attrs, handle alias, etc.
        for subcommand in map_by_cmd:
            builder_list: typing.List[_SubCommandBuilder] = map_by_cmd[subcommand]
            if len(builder_list) > 1: # has alias
                names = [x.name for x in builder_list]
                origin_name = options.find_origin_name(subcommand, names)
                assert origin_name in names, 'the origin name must in `names`'
                origin = [x for x in builder_list if x.name == origin_name][0]
                alias  = [x for x in builder_list if x.name != origin_name]
                assert len(alias) < len(names)
                alias_str = ", ".join(x.formated_name for x in alias)

                for builder in builder_list:
                    sub_attrs = builder.attrs
                    if origin_name == builder.name:
                        sub_attrs['help'] += f'\n (alias: {alias_str})'
                    else: # is alias
                        sub_attrs['help'] += f'\n (alias of: {origin.formated_name})'
                        # must use default command name to call
                        sub_attrs['name'] = builder.formated_name
                        # hide alias:
                        sub_attrs['hidden'] = True

        # add subcommands into group
        for item in user_commands:
            if isinstance(item, _SubCommandBuilder):
                if item.is_group:
                    builded_command = make_group(item.command, item.attrs)
                else:
                    is_objectmethod = not isinstance(item.command, (classmethod, staticmethod))
                    if is_objectmethod:
                        callable_wrapper = _create_method_wrapper(item.command)
                    else:
                        callable_wrapper = item.command
                    adapter = CallableAdapter(callable_wrapper)
                    adapter.args_adapters.extend(ArgumentAdapter.from_callable(item.command))
                    if is_objectmethod:
                        adapter.args_adapters.pop(0) # remove arg `self`
                    builded_command = click.command(**item.attrs)(adapter.get_wrapped_func())
                group.add_command(builded_command)
            else:
                group.add_command(*item)

        return group

    def warpper(cls) -> click.Group:
        attrs: dict = get_attrs(cls)
        attrs.setdefault('name', options.group_name_format(cls, cls.__name__))
        return make_group(cls, attrs)

    return warpper(cls) if cls else warpper
