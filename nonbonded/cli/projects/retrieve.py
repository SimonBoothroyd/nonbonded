from typing import List, Type, Union

import click
from click_option_group import optgroup

from nonbonded.cli.projects.utilities import extract_identifiers, identifiers_options
from nonbonded.cli.utilities import generate_click_command
from nonbonded.library.factories.inputs import InputFactory
from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study


def _retrieve_options() -> List[click.option]:

    return [
        click.option(
            "--results/--no-results",
            "include_results",
            default=False,
            help="Whether to also pull down any available results.",
            show_default=True,
        ),
        optgroup.group(
            "Job submission", help="Options for generating job submission scripts."
        ),
        optgroup.option(
            "--conda-environment",
            default="forcebalance",
            type=click.STRING,
            help="The conda environment to run within.",
            show_default=True,
        ),
        optgroup.option(
            "--max-time",
            default="168:00",
            type=click.STRING,
            help="The maximum wall-clock time for submissions.",
            show_default=True,
        ),
        optgroup.group(
            "Evaluator configuration",
            help="Configuration options for the OpenFF Evaluator.",
        ),
        optgroup.option(
            "--preset",
            "evaluator_preset",
            default="lilac-dask",
            type=click.Choice(["lilac-dask", "lilac-local"], case_sensitive=True),
            help="The present evaluator compute settings to use.",
            show_default=True,
        ),
        optgroup.option(
            "--port",
            "evaluator_port",
            default=8000,
            type=click.INT,
            help="The port to run the evaluator server on.",
            show_default=True,
        ),
        optgroup.option(
            "--workers",
            "n_evaluator_workers",
            default=1,
            type=click.INT,
            help="The target number of evaluator compute workers to spawn.\n"
            "\n"
            "The actual number may be less than this if the specified compute backend "
            "supports elastic scaling of workers depending on the amount of available "
            "work.",
            show_default=True,
        ),
    ]


def retrieve_command(model_type: Type[Union[Project, Study, Optimization, Benchmark]]):
    def base_function(**kwargs):

        # Create the directory structure.
        model = model_type.from_rest(**extract_identifiers(model_type, kwargs))
        model_factory = InputFactory.model_type_to_factory(model_type)

        model_factory.generate(model=model, **kwargs)

    return generate_click_command(
        click.command(
            "retrieve",
            help=f"Retrieve a {model_type.__name__.lower()} from the RESTful API.",
        ),
        [*identifiers_options(model_type), *_retrieve_options()],
        base_function,
    )
