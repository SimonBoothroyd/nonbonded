import click

from nonbonded.cli.benchmark import benchmark
from nonbonded.cli.dataset import dataset
from nonbonded.cli.optimization import optimization
from nonbonded.cli.rest import rest


@click.group()
def cli():
    pass


cli.add_command(benchmark)
cli.add_command(dataset)
cli.add_command(optimization)
cli.add_command(rest)
