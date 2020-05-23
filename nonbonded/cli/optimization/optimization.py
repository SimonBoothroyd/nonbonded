import click

from nonbonded.cli.optimization.analyze import analyze
from nonbonded.cli.optimization.generate import generate
from nonbonded.cli.optimization.retrieve import retrieve
from nonbonded.cli.optimization.run import run


@click.group()
def optimization():
    pass


optimization.add_command(analyze)
optimization.add_command(generate)
optimization.add_command(retrieve)
optimization.add_command(run)
