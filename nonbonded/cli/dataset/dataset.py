import click

from nonbonded.cli.dataset.curate import curate
from nonbonded.cli.dataset.list import list_data_sets
from nonbonded.cli.dataset.retrieve import retrieve


@click.group()
def dataset():
    pass


dataset.add_command(curate)
dataset.add_command(list_data_sets)
dataset.add_command(retrieve)
