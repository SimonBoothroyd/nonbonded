import click

from nonbonded.library.models.projects import Benchmark
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(help="Launch the main RESTful API server.")
@click.option(
    "--project-id",
    type=click.STRING,
    help="The id of the project which the benchmark to retrieve is part of.",
)
@click.option(
    "--study-id",
    type=click.STRING,
    help="The id of the study which the benchmark to retrieve is part of.",
)
@click.option(
    "--benchmark-id", type=click.STRING, help="The id of the benchmark to retrieve.",
)
@click.option(
    "--output",
    required=False,
    type=click.Path(dir_okay=False),
    help="The (optional) path to save the output to.",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the server logger.",
    show_default=True,
)
def retrieve(project_id, study_id, benchmark_id, output, log_level):

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    benchmark = Benchmark.from_rest(
        project_id=project_id, study_id=study_id, benchmark_id=benchmark_id
    )
    benchmark_json = benchmark.json()

    if output is None:

        print(benchmark_json)
        return

    with open(output, "w") as file:
        file.write(benchmark_json)
