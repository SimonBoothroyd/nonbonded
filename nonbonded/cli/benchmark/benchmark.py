import click

from nonbonded.cli.benchmark.analyze import analyze
from nonbonded.cli.benchmark.generate import generate
from nonbonded.cli.benchmark.plot import plot
from nonbonded.cli.benchmark.results import results
from nonbonded.cli.benchmark.retrieve import retrieve
from nonbonded.cli.benchmark.run import run
from nonbonded.cli.benchmark.upload import upload


@click.group()
def benchmark():
    """The stub group for the benchmark commands."""


benchmark.add_command(analyze)
benchmark.add_command(generate)
benchmark.add_command(plot)
benchmark.add_command(results)
benchmark.add_command(retrieve)
benchmark.add_command(run)
benchmark.add_command(upload)
