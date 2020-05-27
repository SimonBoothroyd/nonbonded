import click

from nonbonded.cli.benchmark import benchmark
from nonbonded.cli.dataset import dataset
from nonbonded.cli.optimization import optimization
from nonbonded.cli.project import project
from nonbonded.cli.rest import rest
from nonbonded.cli.study import study


@click.group()
def cli():
    pass


cli.add_command(benchmark)
cli.add_command(dataset)
cli.add_command(optimization)
cli.add_command(project)
cli.add_command(rest)
cli.add_command(study)
