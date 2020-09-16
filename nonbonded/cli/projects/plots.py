from typing import List, Type, Union

import click
from click_option_group import optgroup

from nonbonded.cli.utilities import generate_click_command
from nonbonded.library.factories.plots import PlotFactory
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study


def _plot_options() -> List[click.option]:

    return [
        click.argument(
            "directories",
            nargs=-1,
            type=click.Path(exists=True),
        ),
        optgroup.group(
            "Output",
            help="Options for saving the plots.",
        ),
        optgroup.option(
            "--file-type",
            type=click.Choice(["pdf", "png"]),
            default="pdf",
            show_default=True,
            help="The file type to save the plots as.",
        ),
    ]


def plot_command(model_type: Type[Union[Project, Study, Optimization, Benchmark]]):
    def base_function(**kwargs):

        if len(kwargs.get("directories", [])) == 0:
            kwargs["directories"] = ("",)

        model_factory = PlotFactory.model_type_to_factory(model_type)
        model_factory.plot(**kwargs)

    model_string = (
        "optimizations" if issubclass(model_type, Optimization) else "benchmarks"
    )

    return generate_click_command(
        click.command(
            "plot",
            help=f"Plots the output of a set of {model_string}.\n\n"
            # "File paths to the directories which contain the optimizations to "
            # "plot. These should be directories which contain an 'optimization.json' "
            # "file. The current directory will be used if none are provided.",
        ),
        [*_plot_options()],
        base_function,
    )
