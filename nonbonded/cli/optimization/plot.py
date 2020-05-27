import os

import click

from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.plotting.optimization import plot_results
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(help="Plot the results of the optimization.")
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

    # Load in the optimization and the results.
    optimization = Optimization.parse_file("optimization.json")
    optimization_result = OptimizationResult.parse_file(
        os.path.join("analysis", "optimization-results.json")
    )

    # Create an output directory
    output_directory = "plots"
    os.makedirs(output_directory, exist_ok=True)

    # Plot the results
    plot_results(
        optimizations=[optimization],
        optimization_results=[optimization_result],
        output_directory=output_directory,
    )
