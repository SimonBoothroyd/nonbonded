import os

import click

from nonbonded.cli.options.evaluator import (
    ComputeResources,
    DaskHPCClusterConfig,
    DaskLocalClusterConfig,
    EvaluatorServerConfig,
    QueueWorkerResources,
)
from nonbonded.library.models.datasets import DataSet
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.templates.submission import Submission, SubmissionTemplate
from nonbonded.library.utilities.logging import (
    get_log_levels,
    setup_timestamp_logging,
    string_to_log_level,
)


@click.command(help="Generates the input files for a specified benchmark.")
@click.option(
    "--project-id",
    type=click.STRING,
    help="The id of the project which the benchmark to is part of.",
)
@click.option(
    "--study-id",
    type=click.STRING,
    help="The id of the study which the benchmark is part of.",
)
@click.option(
    "--benchmark-id", type=click.STRING, help="The id of the benchmark.",
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
    benchmark_id,
    backend_name,
    environment_name,
    port,
    max_workers,
    max_wall_clock,
    max_memory,
    log_level,
):

    from openforcefield.typing.engines.smirnoff import ForceField

    # Set up logging if requested.
    logging_level = string_to_log_level(log_level)

    if logging_level is not None:
        setup_timestamp_logging(logging_level)

    # Retrieve the benchmark
    benchmark: Benchmark = Benchmark.from_rest(project_id, study_id, benchmark_id)

    root_directory = benchmark_id
    os.makedirs(root_directory, exist_ok=True)

    # Save the benchmark definition in the directory
    benchmark_path = os.path.join(root_directory, "benchmark.json")

    with open(benchmark_path, "w") as file:
        file.write(benchmark.json())

    # Retrieve the force field.
    if benchmark.force_field_name is not None:
        force_field = ForceField(benchmark.force_field_name)
    else:
        optimization_results: OptimizationResult = OptimizationResult.from_rest(
            project_id=project_id, study_id=study_id, id=benchmark.optimization_id
        )
        force_field = optimization_results.refit_force_field.to_openff()

    force_field.to_file("force-field.offxml", io_format="offxml")

    # Retrieve the data set.
    test_set: DataSet = DataSet.from_rest(benchmark.test_set_id)

    with open("test-set-definition.json", "w") as file:
        file.write(test_set.json())

    evaluator_set = test_set.to_evaluator()
    evaluator_set.json("test-set.json")

    # Generate a server configuration
    if backend_name == "lilac-local":

        backend_config = DaskLocalClusterConfig(resources_per_worker=ComputeResources())

    elif backend_name == "lilac-dask":

        backend_config = DaskHPCClusterConfig(
            maximum_workers=max_workers,
            resources_per_worker=QueueWorkerResources(),
            queue_name="gpuqueue",
            setup_script_commands=[
                f"conda activate {environment_name}",
                "module load cuda/10.1",
            ],
        )

    else:
        raise NotImplementedError()

    server_config = EvaluatorServerConfig(backend_config=backend_config, port=port)

    with open(os.path.join(root_directory, "server-config.json"), "w") as file:
        file.write(server_config.json())

    # Create a job submission file
    submission_path = os.path.join(root_directory, "submit.sh")

    submission = Submission(
        job_name="optim",
        wall_clock_limit=max_wall_clock,
        max_memory=max_memory,
        gpu=backend_name == "lilac-local",
        environment_name=environment_name,
        commands=[
            "nonbonded benchmark run --config server-config.json",
            "nonbonded benchmark analyze",
        ],
    )

    submission_content = SubmissionTemplate.generate("submit_lilac.txt", submission)

    with open(submission_path, "w") as file:
        file.write(submission_content)
