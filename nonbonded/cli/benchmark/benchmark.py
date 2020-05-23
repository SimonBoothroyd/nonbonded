import click

from nonbonded.cli.benchmark.analyze import analyze
from nonbonded.cli.benchmark.generate import generate
from nonbonded.cli.benchmark.retrieve import retrieve
from nonbonded.cli.benchmark.run import run


@click.group()
def benchmark():
    pass


benchmark.add_command(analyze)
benchmark.add_command(generate)
benchmark.add_command(retrieve)
benchmark.add_command(run)
