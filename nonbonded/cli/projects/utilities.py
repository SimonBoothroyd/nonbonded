from typing import Dict, List, Type, Union

import click

from nonbonded.library.models.projects import Benchmark, Optimization, Project, Study


def extract_identifiers(
    model_type: Type[Union[Project, Study, Optimization, Benchmark]], kwargs
) -> Dict[str, str]:
    """Retrieves the identifiers from a list of ``kwargs`` associated with
    a particular model type.
    """

    expected_identifiers = ["project_id"]

    if not issubclass(model_type, Project):
        expected_identifiers.append("study_id")
    if issubclass(model_type, Optimization):
        expected_identifiers.append("optimization_id")
    if issubclass(model_type, Benchmark):
        expected_identifiers.append("benchmark_id")

    identifiers = {
        expected_identifier: kwargs.pop(expected_identifier)
        for expected_identifier in expected_identifiers
    }

    return identifiers


def identifiers_options(
    model_type: Type[Union[Project, Study, Optimization, Benchmark]]
) -> List[click.option()]:
    """Returns required click options to specify the identity of a model of a
    particular type."""

    model_name = model_type.__name__.lower()

    parents = {
        Project: [],
        Study: ["project"],
        Benchmark: ["project", "study"],
        Optimization: ["project", "study"],
    }

    return [
        *[
            click.option(
                f"--{parent}-id",
                type=click.STRING,
                required=True,
                help=f"The id of the parent {parent}.",
            )
            for parent in parents[model_type]
        ],
        click.option(
            f"--{model_name}-id",
            type=click.STRING,
            required=True,
            help=f"The id of the {model_name} to retrieve.",
        ),
    ]
