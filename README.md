# click-anno

![GitHub](https://img.shields.io/github/license/Cologler/click-anno-python.svg)
[![Build Status](https://travis-ci.com/Cologler/click-anno-python.svg?branch=master)](https://travis-ci.com/Cologler/click-anno-python)
[![PyPI](https://img.shields.io/pypi/v/click_anno.svg)](https://pypi.org/project/click-anno/)

use annotation to create click app.

## Compare with click api

### Basic Arguments

``` py
# click
import click

@click.command()
@click.argument('filename')
def touch(filename):
    click.echo(filename)

# click_anno
import click
import click_anno

@click_anno.command
def touch(filename):
    click.echo(filename)
```

### Variadic Arguments

``` py
# click
import click

@click.command()
@click.argument('src', nargs=-1)
@click.argument('dst', nargs=1)
def copy(src, dst):
    for fn in src:
        click.echo('move %s to folder %s' % (fn, dst))

# click_anno
import click
import click_anno

@click_anno.command
def copy(src: tuple, dst):
    for fn in src:
        click.echo('move %s to folder %s' % (fn, dst))
```

### Basic Value Options

``` py
# click
import click

@click.command()
@click.option('--n', default=1)
def dots(n):
    click.echo('.' * n)

# click_anno
import click
import click_anno

@click_anno.command
def dots(n=1):
    click.echo('.' * n)
```

### Required Value Options

``` py
# click
import click

@click.command()
@click.option('--n', required=True, type=int)
def dots(n):
    click.echo('.' * n)

# click_anno
import click
import click_anno

@click_anno.command
def dots(*, n: int):
    click.echo('.' * n)
```

### Multi Value Options

``` py
# click
import click

@click.command()
@click.option('--pos', nargs=2, type=float)
def findme(pos):
    click.echo('%s / %s' % pos)

# click_anno
from typing import Tuple
import click
import click_anno

@click_anno.command
def findme(*, pos: Tuple[float, float]):
    click.echo('%s / %s' % pos)
```

### Tuples as Multi Value Options

``` py
# click
import click

@click.command()
@click.option('--item', type=(str, int))
def putitem(item):
    click.echo('name=%s id=%d' % item)

# click_anno
from typing import Tuple
import click
import click_anno

@click_anno.command
def putitem(*, item: (str, int)):
    click.echo('name=%s id=%d' % item)

# or
@click_anno.command
def putitem(*, item: Tuple[str, int]):
    click.echo('name=%s id=%d' % item)
```

### Boolean Flags

``` py
# click
import click

@click.command()
@click.option('--shout', is_flag=True)
def info(shout):
    click.echo(f'{shout!r}')

# click_anno
import click
from click_anno import command
from click_anno.types import flag

@command
def func(shout: flag):
    click.echo(f'{shout!r}')
```

### Inject Context

``` py
# click
@command()
@click.pass_context
def sync(ctx): # `ctx` must be the 1st arg
    click.echo(str(type(ctx)))

# click_anno
@command
def sync(a, ctx: click.Context, b): # `ctx` can be any location
    click.echo(str(type(ctx)))
```

### Group

``` py
# click
@click.group()
def cli():
    click.echo('Running')

@cli.command()
def sync():
    click.echo('Syncing')

# click_anno
@click_app
class App:
    def __init__(self):
        click.echo('Running')

    def sync(self):
        click.echo('Syncing')
```

### Group Invocation Without Command

``` py
# click
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo('I was invoked without subcommand')
    else:
        click.echo('I am about to invoke %s' % ctx.invoked_subcommand)

@cli.command()
def sync():
    click.echo('The subcommand')

# click_anno
@click_app
@attrs(invoke_without_command=True)
class App:
    def __init__(self, ctx: click.Context):
        if ctx.invoked_subcommand is None:
            click.echo('I was invoked without subcommand')
        else:
            click.echo('I am about to invoke %s' % ctx.invoked_subcommand)

    def sync(self):
        click.echo('The subcommand')
```

## Extensions

### Enum

Enum is **NOT** `Choice`.

``` py
# click
# does not support

# click_anno
import click
from click_anno import command
from enum import Enum, auto

class HashTypes(Enum):
    md5 = auto()
    sha1 = auto()

@command
def digest(hash_type: HashTypes):
    assert isinstance(hash_type, HashTypes)
    click.echo(hash_type)
```

### Alias

``` py
# click
# does not support

# click_anno
@click_app
class App:
    def sync(self):
        click.echo('Syncing')

    alias = sync
```

### show default in argument

by default, `click.argument` did not accept `show_default` option.

click_anno was modify this.

``` py
@command
def func(a=10, *_):
    pass

# with --help
# Usage: func [OPTIONS] [A=10]
# ...
```

## Arguments vs Options

click only has two kinds of parameters:

* Options
* Arguments - work similarly to options but are positional.

By default in python, arguments like `*args` and options like `**kwargs`.

In example `func(a, b=1, *args, d, e=2)`, `a` `b` `args` are arguments, `d` `e` are options.

If you don't want the args `*args`, rename it to `*_`.
**click_anno will ignore all args named `_`**

In example `func(a, b=1)`, `*args` did not exists. so `a` is argument, `b` is option.

## Auto Inject Arguments

by default, you can inject `click.Context` by annotation:

``` py
@command
def inject_context(a, ctx: click.Context, b): # `ctx` can be any location
    click.echo(str(type(ctx)))
```

or impl the `Injectable`:

``` py
from click_anno import Injectable

class Custom(Injectable):
    @classmethod
    def __inject__(cls):
        return cls()

@command
def inject_it(obj: Custom):
    assert isinstance(obj, Custom)
```

or call `inject` function:

``` py
from click_anno import inject

class Custom: pass

inject(Custom, lambda: Custom())

@command
def inject_it(obj: Custom):
    assert isinstance(obj, Custom)
```

or if you want to inject from `click.Context.ensure_object()` or `click.Context.find_object()`, you can use:

``` py
from click_anno import find, ensure

@command
def inject_it(f: find(A), e: ensure(B)):
    ...
```
