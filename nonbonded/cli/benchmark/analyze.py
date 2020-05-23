import logging
import os

import click

from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)

logger = logging.getLogger(__name__)


@click.command(help="Analyzes the output of a benchmark.")
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def analyze(log_level):

    from openff.evaluator.client import RequestResult
    from openff.evaluator.datasets import PhysicalPropertyDataSet

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    # Load in the definition of the benchmark to optimize.
    benchmark = Benchmark.parse_file("benchmark.json")

    # Create a directory to store the results in
    output_directory = "analysis"
    os.makedirs(output_directory, exist_ok=True)

    # Load the reference data set
    reference_data_set = PhysicalPropertyDataSet.from_json("test-set.json")

    # Load in the request results.
    request_results: RequestResult = RequestResult.from_json("results.json")

    if len(request_results.unsuccessful_properties) > 0:

        logger.warning(
            f"{len(request_results.unsuccessful_properties)} could not be estimated."
        )

        for exception in request_results.exceptions:
            logger.warning(str(exception))

    estimated_data_set = request_results.estimated_properties

    # Generate statistics for the estimated properties.
    benchmark_results = BenchmarkResult.from_evaluator(
        project_id=benchmark.project_id,
        study_id=benchmark.study_id,
        benchmark_id=benchmark.id,
        reference_data_set=reference_data_set,
        estimated_data_set=estimated_data_set,
        analysis_environments=benchmark.analysis_environments,
    )

    # Save the results
    with open(os.path.join(output_directory, "benchmark-results.json"), "w") as file:
        file.write(benchmark_results.json())
