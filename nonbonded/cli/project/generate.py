import logging

import click

from nonbonded.library.factories.projects.project import ProjectFactory
from nonbonded.library.models.projects import Project
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)

logger = logging.getLogger(__name__)


@click.command(help="Generates the input files for a specified benchmark.")
@click.option(
    "--project-id",
    type=click.STRING,
    help="The id of the project which the benchmark to is part of.",
)
@click.option(
    "--backend",
    "backend_name",
    default="lilac-dask",
    type=click.Choice(["lilac-dask", "lilac-local"], case_sensitive=True),
    help="The name of the backend to perform the benchmark using.",
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
    backend_name,
    environment_name,
    max_workers,
    max_wall_clock,
    max_memory,
    log_level,
):

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    # Retrieve the benchmark
    project: Project = Project.from_rest(project_id=project_id)

    ProjectFactory.generate(
        project,
        backend_name,
        environment_name,
        max_workers,
        max_wall_clock,
        max_memory,
    )
