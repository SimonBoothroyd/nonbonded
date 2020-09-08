import click

from nonbonded.cli import rest
from nonbonded.cli.projects.projects import benchmark, optimization, project, study


@click.group()
def cli():
    pass


cli.add_command(project)
cli.add_command(study)
cli.add_command(benchmark)
cli.add_command(optimization)

# cli.add_command(dataset)

cli.add_command(rest.rest)
