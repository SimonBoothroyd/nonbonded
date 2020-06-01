import os
from typing import List

from nonbonded.cli.options.evaluator import (
    ComputeResources,
    DaskHPCClusterConfig,
    DaskLocalClusterConfig,
    EvaluatorServerConfig,
    QueueWorkerResources,
)
from nonbonded.library.models.datasets import DataSet, DataSetCollection
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.templates.submission import Submission, SubmissionTemplate


class BenchmarkFactory:
    """An factory used to create the directory structure and
    inputs for a particular benchmark.
    """

    @classmethod
    def generate(
        cls,
        benchmark: Benchmark,
        backend_name: str,
        environment_name: str,
        port: int,
        max_workers: int,
        max_wall_clock: str,
        max_memory: int,
    ):

        from openff.evaluator.client import RequestOptions
        from openforcefield.typing.engines.smirnoff import ForceField

        root_directory = benchmark.id
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
                project_id=benchmark.project_id,
                study_id=benchmark.study_id,
                id=benchmark.optimization_id,
            )
            force_field = optimization_results.refit_force_field.to_openff()

        force_field.to_file(
            os.path.join(root_directory, "force-field.offxml"), io_format="offxml"
        )

        # Retrieve the data set.
        test_sets: List[DataSet] = [
            DataSet.from_rest(x) for x in benchmark.test_set_ids
        ]
        test_set_collection = DataSetCollection(data_sets=test_sets)

        with open(
            os.path.join(root_directory, "test-set-collection.json"), "w"
        ) as file:
            file.write(test_set_collection.json())

        evaluator_set = test_set_collection.to_evaluator()
        evaluator_set.json(os.path.join(root_directory, "test-set.json"))

        # Generate a server configuration
        if backend_name == "lilac-local":

            backend_config = DaskLocalClusterConfig(
                resources_per_worker=ComputeResources()
            )

        elif backend_name == "lilac-dask":

            # noinspection PyTypeChecker
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
                "nonbonded benchmark run --config server-config.json --restart true",
                "nonbonded benchmark analyze",
            ],
        )

        submission_content = SubmissionTemplate.generate("submit_lilac.txt", submission)

        with open(submission_path, "w") as file:
            file.write(submission_content)

        # Generate a set of request options
        request_options = RequestOptions()
        request_options.calculation_layers = ["SimulationLayer"]
        request_options.json("estimation-options.json", format=True)
