import os
from typing import List, Type, Union

import click

from nonbonded.cli.utilities import generate_click_command
from nonbonded.library.models.projects import Benchmark, Optimization
from nonbonded.library.models.results import BenchmarkResult, OptimizationResult


def _upload_options() -> List[click.option]:
    return []


def upload_command(model_type: Type[Union[Optimization, Benchmark]]):

    result_type = (
        OptimizationResult if issubclass(model_type, Optimization) else BenchmarkResult
    )

    def base_function(**_):

        results_name = (
            "optimization" if issubclass(model_type, Optimization) else "benchmark"
        )
        results_path = os.path.join("analysis", f"{results_name}-results.json")

        results = result_type.parse_file(results_path).upload()

        with open(results_path, "w") as file:
            file.write(results.json())

    model_string = (
        "an optimization" if issubclass(model_type, Optimization) else "a benchmark"
    )

    return generate_click_command(
        click.command(
            "upload",
            help=f"Upload the analysed results of {model_string} to the REST API.",
        ),
        [*_upload_options()],
        base_function,
    )
