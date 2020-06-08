import click

from nonbonded.cli.project.generate import generate
from nonbonded.cli.project.list import list_projects
from nonbonded.cli.project.retrieve import retrieve


@click.group()
def project():
    """The stub group for the project commands."""


project.add_command(generate)
project.add_command(list_projects)
project.add_command(retrieve)
