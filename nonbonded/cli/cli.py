import click

from nonbonded.cli.dataset import dataset
from nonbonded.cli.rest import rest


@click.group()
def cli():
    pass


cli.add_command(dataset)
cli.add_command(rest)
