import click

from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(help="Upload the analysed results of a benchmark to the REST API.")
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def upload(log_level):

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    benchmark_results_path = "benchmark-results.json"
    benchmark_results = BenchmarkResult.parse_file(benchmark_results_path)

    benchmark_results = benchmark_results.upload()

    with open(benchmark_results_path, "w") as file:
        file.write(benchmark_results.json())
