import logging
import os
from typing import TYPE_CHECKING, Optional, Tuple, Union

import click
from click_option_group import optgroup

from nonbonded.cli.utilities import generate_click_command
from nonbonded.library.factories.inputs.evaluator import EvaluatorServerConfig

logger = logging.getLogger(__name__)

if TYPE_CHECKING:

    from openff.evaluator.client import RequestOptions, RequestResult
    from openff.evaluator.datasets import PhysicalPropertyDataSet
    from openff.evaluator.forcefield import ForceFieldSource
    from openforcefield.typing.engines.smirnoff import ForceField


def _run_options():

    return [
        click.option(
            "--restart",
            default=True,
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
            type=click.Path(exists=True, dir_okay=False),
            help="The path to the OpenFF Evaluator server configuration file.",
            show_default=True,
        ),
        optgroup.option(
            "--options",
            "request_options",
            default="estimation-options.json",
            type=click.Path(exists=True, dir_okay=False),
            help="The path to the OpenFF Evaluator request options.",
            show_default=True,
        ),
        optgroup.option(
            "--polling-interval",
            default=600,
            type=click.INT,
            help="The interval with which to check the progress of the benchmark (s).",
            show_default=True,
        ),
    ]


def _prepare_restart(
    restart: bool,
) -> Tuple["PhysicalPropertyDataSet", Optional["RequestResult"]]:
    """Prepare the requisite files for restarting if requested, or give a warning
    if not and files will be overwritten.

    Parameters
    ----------
    restart
        Whether to restart previous calculations.

    Returns
    -------
        The data set to be estimated (in the case of restarts this will be the set
        of un-estimated properties) and any existing results.
    """

    from openff.evaluator.client import RequestResult
    from openff.evaluator.datasets import PhysicalPropertyDataSet

    # Check for existing results files to restart from.
    existing_results: Optional[RequestResult] = None

    if os.path.isfile("results.json"):

        message = "An existing results file was found."

        if not restart:
            message = f"{message} These results will be overwritten."
        else:

            existing_results: RequestResult = RequestResult.from_json("results.json")

            if len(existing_results.unsuccessful_properties) == 0:
                message = (
                    f"{message} All properties were successfully estimated and so "
                    f"this command will now exit."
                )

            else:
                message = (
                    f"{message} {len(existing_results.estimated_properties)} data "
                    f"points were successfully estimated, while "
                    f"{len(existing_results.unsuccessful_properties)} could not be. "
                    f"Attempting to re-estimate these unsuccessful data points."
                )

        logger.info(message)

    # Load in the data set.
    if existing_results is None:
        data_set = PhysicalPropertyDataSet.from_json("test-set.json")
    else:
        data_set = existing_results.unsuccessful_properties

    return data_set, existing_results


def _load_force_field() -> Union["ForceField", "ForceFieldSource"]:
    """Load in the force field to use in the benchmark."""

    from openff.evaluator.forcefield import ForceFieldSource
    from openforcefield.typing.engines.smirnoff import ForceField

    if os.path.isfile("force-field.offxml") and os.path.isfile("force-field.json"):

        raise RuntimeError(
            "Two valid force fields were found: force-field.offxml and "
            "force-field.json"
        )

    elif os.path.isfile("force-field.offxml"):
        force_field = ForceField("force-field.offxml")
    elif os.path.isfile("force-field.json"):
        force_field = ForceFieldSource.from_json("force-field.json")
    else:
        raise RuntimeError(
            "No valid force field could be found. Either a SMIRNOFF force field "
            "(named force-field.offxml) or an OpenFF Evaluator force field source "
            "(named force-field.json) must be present in the current directory."
        )

    return force_field


def _run_calculations(
    data_set: "PhysicalPropertyDataSet",
    force_field: "ForceField",
    polling_interval: int,
    request_options: "RequestOptions",
    server_config: EvaluatorServerConfig,
) -> "RequestResult":
    """Attempt to estimate the data set using the specified force field.

    Parameters
    ----------
    data_set
        The data set to estimate.
    force_field
        The force field to estimate the data set with.
    polling_interval
        The interval with which to attempt to retrieve the results.
    request_options
        The options to use when estimating the data set.
    server_config
        The configuration to use for the evaluator server.
    """
    from openff.evaluator.client import ConnectionOptions, EvaluatorClient

    calculation_backend = server_config.to_backend()

    with calculation_backend:

        evaluator_server = server_config.to_server(calculation_backend)

        with evaluator_server:

            # Request the estimates.
            client = EvaluatorClient(ConnectionOptions(server_port=server_config.port))

            request, error = client.request_estimate(
                property_set=data_set,
                force_field_source=force_field,
                options=request_options,
            )

            if error is not None:
                raise error

            # Wait for the results.
            results, error = request.results(True, polling_interval=polling_interval)

            if error is not None:
                raise error

    return results


def run_command():
    def base_function(**kwargs):

        from openff.evaluator.client import RequestOptions

        # Load in the force field.
        force_field = _load_force_field()

        # Load any previous results and the data set to estimate.
        data_set, existing_results = _prepare_restart(kwargs.pop("restart"))

        # Load the server configuration.
        server_config = EvaluatorServerConfig.parse_file(kwargs.pop("server_config"))

        # Load in the request options
        request_options = RequestOptions.from_json(kwargs.pop("request_options"))

        results = _run_calculations(
            data_set,
            force_field,
            kwargs.pop("polling_interval"),
            request_options,
            server_config,
        )

        # Save a copy of the results in case adding the already estimated
        # properties failed for some reason.
        results.json("results.tmp.json")

        if existing_results is not None:

            results.estimated_properties.add_properties(
                *existing_results.estimated_properties.properties,
                validate=False,
            )

        # Save the results to disk.
        results.json("results.json")

        if os.path.isfile("results.tmp.json"):
            # Remove the backup results.
            os.unlink("results.tmp.json")

    return generate_click_command(
        click.command(
            "run",
            help="Run a benchmark in the current directory.\n\nThis directory must "
            "contain all of the required input files.",
        ),
        [*_run_options()],
        base_function,
    )
