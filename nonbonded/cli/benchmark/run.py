import logging
import os
from typing import Optional

import click

from nonbonded.cli.options.evaluator import EvaluatorServerConfig
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)

logger = logging.getLogger(__name__)


@click.command(
    help="Run a benchmark in the current directory.\n\nThis directory "
    "must contain all of the required input files."
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
    "--options",
    "request_options",
    default="estimation-options.json",
    type=click.Path(exists=True, dir_okay=False),
    help="The path to the OpenFF Evaluator request options.",
    show_default=True,
)
@click.option(
    "--polling-interval",
    default=600,
    type=click.INT,
    help="The interval with which to check the progress of the benchmark (s).",
    show_default=True,
)
@click.option(
    "--restart",
    default=True,
    type=click.BOOL,
    help="Whether to restart any failed estimations if found. If false, any "
    "existing results will be overwritten.",
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def run(server_config, request_options, polling_interval: int, restart: bool, log_level):

    from openff.evaluator.client import (
        ConnectionOptions, EvaluatorClient, RequestOptions, RequestResult
    )
    from openff.evaluator.datasets import PhysicalPropertyDataSet

    from openforcefield.typing.engines.smirnoff import ForceField

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

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

                logger.info(message)
                return

            message = (
                f"{message} {len(existing_results.estimated_properties)} data points "
                f"were successfully estimated, while "
                f"{len(existing_results.unsuccessful_properties)} could not be. "
                f"Attempting to re-estimate these unsuccessful data points."
            )

        logger.info(message)

    # Load in the force field.
    force_field = ForceField("force-field.offxml")

    # Load in the data set.
    if existing_results is None:
        data_set = PhysicalPropertyDataSet.from_json("test-set.json")
    else:
        data_set = existing_results.unsuccessful_properties

    server_config = EvaluatorServerConfig.parse_file(server_config)

    # Load in the request options
    request_options = RequestOptions.parse_json(request_options)

    calculation_backend = server_config.to_backend()

    with calculation_backend:

        evaluator_server = server_config.to_server(calculation_backend)

        with evaluator_server:

            # Request the estimates.
            client = EvaluatorClient(ConnectionOptions(server_port=server_config.port))

            request, error = client.request_estimate(
                property_set=data_set,
                force_field_source=force_field,
                options=request_options
            )

            if error is not None:
                raise Exception(str(error))

            # Wait for the results.
            results, error = request.results(True, polling_interval=polling_interval)

            if error is not None:
                raise Exception(str(error))

            # Save a copy of the results in case adding the already estimated
            # properties failed for some reason.
            results.json("results.tmp.json")

            if existing_results is not None:

                results.estimated_properties.add_properties(
                    *existing_results.estimated_properties.properties, validate=False
                )

            # Save the results to disk.
            results.json("results.json")

            if os.path.isfile("results.tmp.json"):
                # Remove the backup results.
                os.unlink("results.tmp.json")
