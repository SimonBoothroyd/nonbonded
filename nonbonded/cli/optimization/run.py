import logging
import os
import shutil
from glob import glob
from subprocess import check_call

import click

from nonbonded.cli.options.evaluator import EvaluatorServerConfig
from nonbonded.library.models.projects import Optimization
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)

logger = logging.getLogger(__name__)


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
    "--restart",
    default=True,
    type=click.BOOL,
    help="Whether to restart the optimization from where it left off if one was "
    "already in progress and failed. If false, any existing results will be "
    "overwritten.",
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def run(server_config, restart: bool, log_level):

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    # Load in the optimization being performed.
    optimization = Optimization.parse_file("optimization.json")

    # Remove any residual files if not restarting.
    should_restart = False

    if not restart:

        restart_files = [
            "optimize.tmp",
            "optimize.bak",
            "optimize.sav",
            "result",
            "worker-logs",
            "working-data",
        ]

        for restart_file in restart_files:

            if os.path.isdir("optimize.tmp") or os.path.isfile(restart_file):

                logger.info(f"Removing {restart_file} as restarting is disabled.")

                if os.path.isdir(restart_file):
                    shutil.rmtree(restart_file)
                else:
                    os.unlink(restart_file)

    else:

        target_name = optimization.force_balance_input.target_name

        previous_iteration_directories = glob(
            os.path.join("optimize.tmp", target_name, "iter_*")
        )

        if (
            not os.path.isfile("optimize.sav")
            and len(previous_iteration_directories) > 0
        ):

            raise Exception(
                "Previous optimization ouput directories were found but optimize.sav "
                "was not."
            )

        if os.path.isfile("optimize.sav") and len(previous_iteration_directories) == 0:

            raise Exception(
                "An optimize.sav file was found but no optimization output directories "
                "could be found."
            )

        n_iterations = len(previous_iteration_directories)

        if n_iterations > 0:

            should_restart = True

            for iteration in range(n_iterations):

                expected_directory = os.path.join(
                    "optimize.tmp", target_name, "iter_" + str(iteration).zfill(4)
                )

                if not os.path.isdir(expected_directory):
                    raise Exception(f"The {expected_directory} directory is missing.")

            final_directory = os.path.join(
                "optimize.tmp", target_name, "iter_" + str(n_iterations - 1).zfill(4)
            )

            if not os.path.isfile(os.path.join(final_directory, "results.json")):
                # Remove the last directory if it did not contain a results file.
                shutil.rmtree(final_directory)
                n_iterations -= 1

            logger.info(
                f"{n_iterations} iterations had previously been completed. "
                f"The optimization will be restarted from iteration {n_iterations}"
            )

    server_config = EvaluatorServerConfig.parse_file(server_config)

    calculation_backend = server_config.to_backend()

    force_balance_arguments = ["ForceBalance.py", "optimize.in"]

    if should_restart:
        force_balance_arguments.insert(1, "--continue")

    with calculation_backend:

        evaluator_server = server_config.to_server(calculation_backend)

        with evaluator_server:

            with open("force_balance.log", "w") as file:
                check_call(force_balance_arguments, stderr=file, stdout=file)
