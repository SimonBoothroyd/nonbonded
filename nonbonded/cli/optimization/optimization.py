import click

from nonbonded.cli.optimization.analyze import analyze
from nonbonded.cli.optimization.generate import generate
from nonbonded.cli.optimization.plot import plot
from nonbonded.cli.optimization.retrieve import retrieve
from nonbonded.cli.optimization.run import run
from nonbonded.cli.optimization.upload import upload


@click.group()
def optimization():
    pass


optimization.add_command(analyze)
optimization.add_command(generate)
optimization.add_command(plot)
optimization.add_command(retrieve)
optimization.add_command(run)
optimization.add_command(upload)
