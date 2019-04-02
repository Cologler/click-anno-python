# click-anno

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
