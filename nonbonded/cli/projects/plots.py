from typing import Type, Union

import click

from nonbonded.cli.utilities import generate_click_command
from nonbonded.library.factories.plots import PlotFactory
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study


def plot_command(model_type: Type[Union[Project, Study, Optimization, Benchmark]]):
    def base_function(**kwargs):

        model_factory = PlotFactory.model_type_to_factory(model_type)
        model_factory.plot(**kwargs)

    model_string = (
        "an optimization" if issubclass(model_type, Optimization) else "a benchmark"
    )

    return generate_click_command(
        click.command(
            "plot",
            help=f"Plots the output of {model_string}.",
        ),
        [],
        base_function,
    )
