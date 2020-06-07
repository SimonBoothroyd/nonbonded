import click

from nonbonded.cli.study.generate import generate
from nonbonded.cli.study.results import results
from nonbonded.cli.study.retrieve import retrieve


@click.group()
def study():
    """The stub group for the study commands."""


study.add_command(generate)
study.add_command(results)
study.add_command(retrieve)
