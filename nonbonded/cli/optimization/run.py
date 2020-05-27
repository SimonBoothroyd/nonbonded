from subprocess import check_call

import click

from nonbonded.cli.options.evaluator import EvaluatorServerConfig
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(
    help="Run a ForceBalance optimization in the current directory.\n\nThis directory "
    "must contain all of the required ForceBalance input files."
)
@click.option(
    "--config",
    "server_config",
    default="server-config.json",
    type=click.Path(exists=True, dir_okay=False),
    help="The path to the OpenFF Evaluator server configuration file.",
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def run(server_config, log_level):

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    server_config = EvaluatorServerConfig.parse_file(server_config)

    calculation_backend = server_config.to_backend()

    with calculation_backend:

        evaluator_server = server_config.to_server(calculation_backend)

        with evaluator_server:

            with open("force_balance.log", "w") as file:
                check_call(["ForceBalance.py", "optimize.in"], stdout=file)
