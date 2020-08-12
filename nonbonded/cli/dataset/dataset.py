import click

from nonbonded.cli.dataset.list import list_data_sets
from nonbonded.cli.dataset.retrieve import retrieve


@click.group()
def dataset():
    """The stub group for the dataset commands."""


dataset.add_command(list_data_sets)
dataset.add_command(retrieve)
