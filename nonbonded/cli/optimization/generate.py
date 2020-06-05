import click

from nonbonded.library.factories.projects.optimization import OptimizationFactory
from nonbonded.library.models.projects import Optimization
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(help="Generates the input files for a specified optimization.")
@click.option(
    "--project-id",
    type=click.STRING,
    help="The id of the project which the optimization to is part of.",
)
@click.option(
    "--study-id",
    type=click.STRING,
    help="The id of the study which the optimization is part of.",
)
@click.option(
    "--optimization-id", type=click.STRING, help="The id of the optimization.",
)
@click.option(
    "--backend",
    "backend_name",
    default="lilac-dask",
    type=click.Choice(["lilac-dask", "lilac-local"], case_sensitive=True),
    help="The name of the backend to perform the optimization using.",
    show_default=True,
)
@click.option(
    "--environment",
    "environment_name",
    default="forcebalance",
    type=click.STRING,
    help="The name of the conda environment to run using.",
    show_default=True,
)
@click.option(
    "--port",
    default=8000,
    type=click.INT,
    help="The port to run the evaluator server on.",
    show_default=True,
)
@click.option(
    "--max-workers",
    required=True,
    type=click.INT,
    help="The maximum number of workers to spawn. This option is only used with dask-"
    "jobqueue based backends",
    show_default=True,
)
@click.option(
    "--max-wallclock",
    "max_wall_clock",
    default="168:00",
    type=click.STRING,
    help="The maximum wall-clock time to run for.",
    show_default=True,
)
@click.option(
    "--max-memory",
    default=8,
    type=click.INT,
    help="The maximum memory (GB) to request for the main job.",
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def generate(
    project_id,
    study_id,
    optimization_id,
    backend_name,
    environment_name,
    port,
    max_workers,
    max_wall_clock,
    max_memory,
    log_level,
):

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    # Retrieve the optimization
    optimization: Optimization = Optimization.from_rest(
        project_id=project_id, study_id=study_id, optimization_id=optimization_id
    )

    OptimizationFactory.generate(
        optimization,
        backend_name,
        environment_name,
        port,
        max_workers,
        max_wall_clock,
        max_memory,
    )
