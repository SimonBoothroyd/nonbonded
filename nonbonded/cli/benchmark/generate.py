import click

from nonbonded.library.factories.projects.benchmark import BenchmarkFactory
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(help="Generates the input files for a particular benchmark.")
@click.option(
    "--project-id", type=click.STRING, help="The id of the parent project.",
)
@click.option(
    "--study-id", type=click.STRING, help="The id of the parent study.",
)
@click.option(
    "--benchmark-id",
    type=click.STRING,
    help="The id of the benchmark to generate inputs for.",
)
@click.option(
    "--backend",
    "backend_name",
    default="lilac-dask",
    type=click.Choice(["lilac-dask", "lilac-local"], case_sensitive=True),
    help="The name of the backend to perform calculations with.",
    show_default=True,
)
@click.option(
    "--environment",
    "environment_name",
    default="forcebalance",
    type=click.STRING,
    help="The name of the conda environment to perform calculations with.",
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
    help="The maximum number of workers to spawn. This option is only used "
    "with `dask-jobqueue` based backends",
    show_default=True,
)
@click.option(
    "--max-wallclock",
    "max_wall_clock",
    default="168:00",
    type=click.STRING,
    help="The maximum wall-clock time for any calculations. This is not "
    "the maximum wall-clock time which will be made available to `dask-jobqueue` "
    "workers which is instead defined by the server configuration.",
    show_default=True,
)
@click.option(
    "--max-memory",
    default=8,
    type=click.INT,
    help="The maximum memory (GB) to request for any calculations. This is not "
    "the maximum memory which will be made available to `dask-jobqueue` workers "
    "which is instead defined by the server configuration.",
    show_default=True,
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(get_log_levels()),
    help="The verbosity of the logger.",
    show_default=True,
)
def generate(
    project_id,
    study_id,
    benchmark_id,
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

    # Retrieve the benchmark
    benchmark: Benchmark = Benchmark.from_rest(
        project_id=project_id, study_id=study_id, benchmark_id=benchmark_id
    )

    BenchmarkFactory.generate_inputs(
        benchmark,
        backend_name,
        environment_name,
        port,
        max_workers,
        max_wall_clock,
        max_memory,
    )
