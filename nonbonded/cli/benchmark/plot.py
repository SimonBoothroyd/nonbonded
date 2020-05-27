import os

import click

from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.plotting.benchmark import plot_results
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(help="Plot the results of the benchmark.")
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def plot(log_level):

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    # Load in the benchmark and the results.
    benchmark = Benchmark.parse_file("benchmark.json")
    benchmark_result = BenchmarkResult.parse_file(
        os.path.join("analysis", "benchmark-results.json")
    )

    # Load in the benchmarked data sets
    reference_data_sets = DataSetCollection.parse_file("test-set-collection.json")

    # Create an output directory
    output_directory = "plots"
    os.makedirs(output_directory, exist_ok=True)

    # Plot the results
    plot_results(
        benchmarks=[benchmark],
        benchmark_results=[benchmark_result],
        data_sets=reference_data_sets.data_sets,
        output_directory=output_directory,
    )
