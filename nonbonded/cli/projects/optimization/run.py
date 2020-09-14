import logging
import os
import shutil
from contextlib import contextmanager
from glob import glob
from subprocess import check_call
from typing import Optional

import click
from click_option_group import optgroup

from nonbonded.cli.utilities import generate_click_command
from nonbonded.library.factories.inputs.evaluator import EvaluatorServerConfig
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.targets import EvaluatorTarget

logger = logging.getLogger(__name__)


def _remove_previous_files():
    """Attempts to delete any files generated by a previous run."""

    restart_files = [
        "optimize.tmp",
        "optimize.bak",
        "optimize.sav",
        "result",
        "worker-logs",
        "working-data",
    ]

    for restart_file in restart_files:

        if os.path.isdir(restart_file):
            shutil.rmtree(restart_file)
        elif os.path.isfile(restart_file):
            os.unlink(restart_file)
        else:
            continue

        logger.info(f"Removing {restart_file}.")


def _prepare_restart(optimization: Optimization):
    """Attempts to prepare the directory structure for a restart."""

    # Remove any partially finished result directories.
    for target in optimization.targets:

        iteration_directories = glob(os.path.join("optimize.tmp", target.id, "iter_*"))

        expected_outputs = [
            (iteration_directory, os.path.join(iteration_directory, "objective.p"))
            for iteration_directory in iteration_directories
        ]

        for iteration_directory, objective_path in expected_outputs:

            if os.path.isfile(objective_path):
                continue

            logger.info(
                f"Removing the {iteration_directory} directory which was produced by "
                f"an incomplete iteration."
            )
            shutil.rmtree(iteration_directory)

    # Find the number of iterations which successfully completed.
    complete_iterations = optimization.max_iterations

    for target in optimization.targets:

        iteration_directories = glob(os.path.join("optimize.tmp", target.id, "iter_*"))
        n_iterations = len(iteration_directories)

        expected_directories = [
            os.path.join("optimize.tmp", target.id, "iter_" + str(iteration).zfill(4))
            for iteration in range(n_iterations)
        ]

        missing_directories = {*expected_directories} - {*iteration_directories}

        if len(missing_directories) > 0:

            missing_string = "\n".join(missing_directories)

            raise RuntimeError(
                f"The following output directories of the {target.id} could not be "
                f"found:\n{missing_string}"
            )

        final_directory = os.path.join(
            "optimize.tmp", target.id, "iter_" + str(n_iterations - 1).zfill(4)
        )

        if not os.path.isfile(os.path.join(final_directory, "objective.p")):
            # Remove the last directory if it did not contain an 'objective.p' file.
            n_iterations -= 1

        complete_iterations = min(complete_iterations, n_iterations)

    if complete_iterations > 0:

        logger.info(
            f"{complete_iterations} iterations had previously been completed. "
            f"The optimization will be restarted from iteration {complete_iterations}"
        )

    # Remove any result directories where not all targets finished successfully.
    for target in optimization.targets:

        iteration_directories = glob(os.path.join("optimize.tmp", target.id, "iter_*"))
        expected_directories = [
            os.path.join("optimize.tmp", target.id, "iter_" + str(iteration).zfill(4))
            for iteration in range(complete_iterations)
        ]

        extra_directories = {*iteration_directories} - {*expected_directories}

        for extra_directory in extra_directories:
            shutil.rmtree(extra_directory)


@contextmanager
def _launch_required_services(optimization: Optimization, server_config: Optional[str]):
    """Launches any required services such as an OpenFF Evaluator server."""

    if not any(isinstance(target, EvaluatorTarget) for target in optimization.targets):
        yield
        return

    if server_config is None:

        raise RuntimeError(
            "The path to an OpenFF Evaluator server configuration must be provided "
            "when running an optimization against a physical property data set."
        )

    server_config = EvaluatorServerConfig.parse_file(server_config)
    calculation_backend = server_config.to_backend()

    with calculation_backend:

        evaluator_server = server_config.to_server(calculation_backend)

        with evaluator_server:

            yield


def _run_options():

    return [
        click.option(
            "--restart",
            default=False,
            type=click.BOOL,
            help="Whether to restart the optimization from where it left off.\nIf "
            "false any existing results will be removed / overwritten.",
            show_default=True,
        ),
        optgroup.group(
            "Evaluator configuration",
            help="Configuration options for the OpenFF Evaluator.",
        ),
        optgroup.option(
            "--config",
            "server_config",
            default="server-config.json",
            type=click.Path(exists=False, dir_okay=False),
            help="The path to the OpenFF Evaluator server configuration file.",
            show_default=True,
        ),
    ]


def run_command():
    def base_function(**kwargs):

        restart = kwargs.pop("restart")
        server_config = kwargs.pop("server_config")

        # Load in the optimization being performed.
        optimization = Optimization.parse_file("optimization.json")

        # Remove any residual files if not restarting.
        should_restart = False

        if not restart:
            _remove_previous_files()
        else:

            if not os.path.isfile("optimize.sav"):

                logger.info(
                    "No 'optimize.sav' file was found. It will be assumed that the "
                    "optimization should be started from the beginning."
                )
                _remove_previous_files()

            else:
                _prepare_restart(optimization)
                should_restart = True

        force_balance_arguments = ["ForceBalance.py", "optimize.in"]

        if should_restart:
            force_balance_arguments.insert(1, "--continue")

        with _launch_required_services(optimization, server_config):

            with open("force_balance.log", "w") as file:
                check_call(force_balance_arguments, stderr=file, stdout=file)

    return generate_click_command(
        click.command(
            "run",
            help="Run a ForceBalance optimization in the current directory.\n\nThis "
            "directory must contain all of the required ForceBalance input files.",
        ),
        [*_run_options()],
        base_function,
    )