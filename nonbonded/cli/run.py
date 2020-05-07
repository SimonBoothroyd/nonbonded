import contextlib
import os
from subprocess import check_call

import click

from nonbonded.cli.options.evaluator import EvaluatorServerConfig
from nonbonded.cli.utilities import MutuallyExclusiveOption
from nonbonded.library.utilities.exceptions import (
    InvalidFileObjectError,
    UnrecognisedForceFieldError,
)
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.group()
def run():
    pass


@click.command(
    help="Launches an OpenFF Evaluator server using a specific configuration."
)
@click.option(
    "--server-config",
    type=click.Path(exists=True, dir_okay=False),
    help="The path to the OpenFF Evaluator server configuration file. If one isn't "
    "provided, it will be assumed that an existing server should be connected to.",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["server_address", "server_port"],
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def evaluator(server_config, log_level):

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    server_config: EvaluatorServerConfig = EvaluatorServerConfig.parse_file(
        server_config
    )

    calculation_backend, evaluator_server = server_config.to_evaluator()

    with calculation_backend:
        evaluator_server.start(asynchronous=False)


@click.command(
    help="Evaluate a data set of physical properties against a particular molecular "
    "mechanics force field using the OpenFF Evaluator framework."
)
@click.option(
    "--server-config",
    type=click.Path(exists=True, dir_okay=False),
    help="The path to the OpenFF Evaluator server configuration file. If one isn't "
    "provided, it will be assumed that an existing server should be connected to.",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["server_address", "server_port"],
    show_default=True,
)
@click.option(
    "--server-address",
    type=click.STRING,
    help="The address of an already running OpenFF Evaluator server which should be "
    "used to perform this benchmark.",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["server_config"],
    show_default=True,
)
@click.option(
    "--server-port",
    type=click.INT,
    help="The port of an already running OpenFF Evaluator server which should be "
    "used to perform this benchmark.",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["server_config"],
    show_default=True,
)
@click.option(
    "--force-field",
    default="force-field.json",
    type=click.Path(exists=True, dir_okay=False),
    help="The path to the force field to perform the benchmark using. This should "
    "either by an OpenFF .offxml file, or an OpenFF Evaluator serialized force field "
    "source.",
    show_default=True,
)
@click.option(
    "--data-set",
    default="data-set.json",
    type=click.Path(exists=True, dir_okay=False),
    help="The path to the OpenFF Evaluator data set to benchmark against.",
    show_default=True,
)
@click.option(
    "--output-path",
    default="results.json",
    type=click.Path(exists=False, dir_okay=False),
    help="The path to save the evaluation results to.",
    show_default=True,
)
@click.option(
    "--polling-interval",
    default=600.0,
    type=click.FLOAT,
    help="The frequency with which to poll the server for the status of the request in "
    "seconds.",
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def benchmark(
    server_config,
    server_address,
    server_port,
    force_field,
    data_set,
    output_path,
    polling_interval,
    log_level,
):

    from evaluator.client import ConnectionOptions, EvaluatorClient
    from evaluator.datasets import PhysicalPropertyDataSet
    from evaluator.forcefield import ForceFieldSource
    from openforcefield.typing.engines.smirnoff import ForceField

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    # Load in the force field source
    _, force_field_extension = os.path.splitext(force_field)

    if force_field_extension.lower() == ".offxml":
        force_field_source = ForceField(force_field)

    elif force_field_extension.lower() == ".json":

        force_field_source = ForceFieldSource.from_json(force_field)

        if not isinstance(force_field_source, ForceFieldSource):

            raise InvalidFileObjectError(
                force_field, type(force_field_source), ForceFieldSource
            )
    else:
        raise UnrecognisedForceFieldError(force_field_extension)

    # Load in the data set.
    data_set_object = PhysicalPropertyDataSet.from_json(data_set)

    if not isinstance(data_set_object, PhysicalPropertyDataSet):

        raise InvalidFileObjectError(data_set, type(data_set), PhysicalPropertyDataSet)

    # Spin up an evaluator server if one isn't already running.
    if server_config is not None:

        server_config: EvaluatorServerConfig = EvaluatorServerConfig.parse_file(
            server_config
        )

        server_port = server_config.port
        server_address = "localhost"

        calculation_backend, evaluator_server = server_config.to_evaluator()

    else:

        calculation_backend = contextlib.nullcontext()
        evaluator_server = contextlib.nullcontext()

    with calculation_backend:

        with evaluator_server:

            # Generate the request options.

            # Request the estimates.
            connection_options = ConnectionOptions(server_address, server_port)
            client = EvaluatorClient(connection_options)

            request, _ = client.request_estimate(
                property_set=data_set_object, force_field_source=force_field_source,
            )

            # Wait for the results.
            results, _ = request.results(True, polling_interval)
            results.json(output_path)


@click.command(
    help="Run a ForceBalance optimization in the current directory.\n\nThis directory "
    "must contain all of the required ForceBalance input files."
)
@click.option(
    "--input-path",
    default="optimize.in",
    type=click.Path(exists=True, dir_okay=False),
    help="The path to the ForceBalance input file.",
    show_default=True,
)
@click.option(
    "--server-config",
    default="server-config.jsoj",
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
def optimize(input_path, server_config, log_level):

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    server_config: EvaluatorServerConfig = EvaluatorServerConfig.parse_file(
        server_config
    )

    calculation_backend, evaluator_server = server_config.to_evaluator()

    with calculation_backend:
        with evaluator_server:

            with open("force_balance.log", "w") as file:
                check_call(["ForceBalance.py", input_path], stdout=file)


run.add_command(benchmark)
run.add_command(optimize)
