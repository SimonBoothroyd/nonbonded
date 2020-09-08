import click

from nonbonded.cli.projects.analysis import analyse_command
from nonbonded.cli.projects.benchmark.run import run_command as run_benchmark
from nonbonded.cli.projects.optimization.run import run_command as run_optimization
from nonbonded.cli.projects.plot import plot_command
from nonbonded.cli.projects.retrieve import retrieve_command
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study


@click.group()
def project():
    """The stub group for the project commands."""


project.add_command(retrieve_command(Project))
project.add_command(analyse_command(Project))
project.add_command(plot_command(Project))


@click.group()
def study():
    """The stub group for the study commands."""


study.add_command(retrieve_command(Study))
study.add_command(analyse_command(Study))
study.add_command(plot_command(Study))


@click.group()
def optimization():
    """The stub group for the optimization commands."""


optimization.add_command(retrieve_command(Optimization))
optimization.add_command(analyse_command(Optimization))
optimization.add_command(plot_command(Optimization))
optimization.add_command(run_optimization())


@click.group()
def benchmark():
    """The stub group for the benchmark commands."""


benchmark.add_command(retrieve_command(Benchmark))
benchmark.add_command(analyse_command(Benchmark))
benchmark.add_command(plot_command(Benchmark))
benchmark.add_command(run_benchmark())
