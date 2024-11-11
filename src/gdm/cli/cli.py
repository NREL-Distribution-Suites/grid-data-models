import click
from gdm.cli.reducer import reduce


@click.group()
def cli():
    pass


cli.add_command(reduce)
