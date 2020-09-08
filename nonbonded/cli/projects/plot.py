from typing import Type, Union

import click

from nonbonded.cli.projects.utilities import extract_identifiers, identifiers_options
from nonbonded.cli.utilities import generate_click_command
from nonbonded.library.factories.plots import PlotFactory
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study


def plot_command(model_type: Type[Union[Project, Study, Optimization, Benchmark]]):
    def base_function(**kwargs):

        # Create the directory structure.
        model = model_type.from_rest(**extract_identifiers(model_type, kwargs))
        model_factory = PlotFactory.model_type_to_factory(model_type)

        model_factory.generate(model=model, **kwargs)

    return generate_click_command(
        click.command(
            "plot",
            help="Plots the output of a sub-study (optimization or benchmark).",
        ),
        [*identifiers_options(model_type)],
        base_function,
    )
