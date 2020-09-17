from typing import List, Type, Union

import click
from click_option_group import optgroup

from nonbonded.cli.utilities import generate_click_command
from nonbonded.library.factories.analysis import AnalysisFactory
from nonbonded.library.models.projects import Benchmark, Optimization


def _analyse_options() -> List[click.option]:

    return [
        optgroup.group(
            "Backwards compatibility",
            help="Options to allow for backwards compatibility with previous results.",
        ),
        optgroup.option(
            "--reindex",
            is_flag=True,
            default=False,
            help="Attempt to determine matching reference and estimated data points "
            "based on the state at which the property was measured, rather than by its "
            "unique id. This option is only to allow backwards compatibility with "
            "optimizations ran not using this framework, and should not be used in "
            "general.",
        ),
    ]


def analyze_command(model_type: Type[Union[Optimization, Benchmark]]):
    def base_function(**kwargs):

        model_factory = AnalysisFactory.model_type_to_factory(model_type)
        model_factory.analyze(**kwargs)

    model_string = (
        "an optimization" if issubclass(model_type, Optimization) else "a benchmark"
    )

    return generate_click_command(
        click.command("analyze", help=f"Analyzes the output of {model_string}."),
        [*_analyse_options()],
        base_function,
    )
