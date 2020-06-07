import click

from nonbonded.library.models.projects import Project
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(help="Retrieve a project from the REST API.")
@click.option(
    "--project-id", type=click.STRING, help="The id of the project to retrieve.",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the logger.",
    show_default=True,
)
def retrieve(project_id, log_level):

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    project = Project.from_rest(project_id=project_id)
    print(project.json())
