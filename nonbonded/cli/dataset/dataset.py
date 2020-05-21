import click

from nonbonded.cli.dataset.curate import curate


@click.group()
def dataset():
    pass


dataset.add_command(curate)
