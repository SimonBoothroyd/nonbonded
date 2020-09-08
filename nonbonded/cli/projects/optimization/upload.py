import os

import click

from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(help="Upload the analysed results of an optimization to the REST API.")
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

    optimization_results_path = os.path.join("analysis", "optimization-results.json")
    optimization_results = OptimizationResult.parse_file(optimization_results_path)

    optimization_results = optimization_results.upload()

    with open(optimization_results_path, "w") as file:
        file.write(optimization_results.json())
