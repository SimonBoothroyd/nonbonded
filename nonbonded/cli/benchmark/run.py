import click

from nonbonded.cli.options.evaluator import EvaluatorServerConfig
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


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
    "--polling-interval",
    default=600,
    type=click.INT,
    help="The interval with which to check the progress of the benchmark (s).",
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def run(server_config, polling_interval, log_level):

    from openff.evaluator.client import ConnectionOptions, EvaluatorClient
    from openff.evaluator.datasets import PhysicalPropertyDataSet

    from openforcefield.typing.engines.smirnoff import ForceField

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    # Load in the force field.
    force_field = ForceField("force-field.json")

    # Load in the data set.
    data_set = PhysicalPropertyDataSet.from_json("test-set.json")

    server_config = EvaluatorServerConfig.parse_file(server_config)

    calculation_backend = server_config.to_backend()

    with calculation_backend:

        evaluator_server = server_config.to_server(calculation_backend)

        with evaluator_server:

            # Request the estimates.
            client = EvaluatorClient(ConnectionOptions(server_port=server_config.port))

            request, error = client.request_estimate(
                property_set=data_set, force_field_source=force_field,
            )

            if error is not None:
                raise Exception(str(error))

            # Wait for the results.
            results, error = request.results(True, polling_interval=polling_interval)

            if error is not None:
                raise Exception(str(error))

            # Save the results to disk.
            results.json("results.json")
