import os
from typing import List, Optional, Union

from nonbonded.library.factories.inputs import InputFactory
from nonbonded.library.models.datasets import DataSet, DataSetCollection, QCDataSet
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult, OptimizationResult


class BenchmarkInputFactory(InputFactory):
    """An factory used to create the directory structure and
    inputs for a particular benchmark.
    """

    @classmethod
    def _retrieve_force_field(
        cls, benchmark: Benchmark, optimization_result: Optional[OptimizationResult]
    ):
        """Retrieve the force field to benchmark and store it in the current
        directory.
        """

        from openff.evaluator.forcefield import ForceFieldSource
        from openff.toolkit.typing.engines.smirnoff.forcefield import (
            ForceField as OFFForceField,
        )

        if benchmark.force_field is not None:

            force_field = benchmark.force_field.to_openff()

        else:

            optimization_result = (
                optimization_result
                if optimization_result is not None
                else OptimizationResult.from_rest(
                    project_id=benchmark.project_id,
                    study_id=benchmark.study_id,
                    model_id=benchmark.optimization_id,
                )
            )

            force_field = optimization_result.refit_force_field.to_openff()

        if isinstance(force_field, OFFForceField):
            force_field.to_file("force-field.offxml", io_format="offxml")
        elif isinstance(force_field, ForceFieldSource):
            force_field.json("force-field.json")

    @classmethod
    def _retrieve_data_sets(
        cls,
        benchmark: Benchmark,
        reference_data_sets: Optional[List[Union[DataSet, QCDataSet]]],
    ):
        """Retrieve the data sets to benchmark against from the RESTful API and
        store them in the current directory."""

        test_sets = cls._find_or_retrieve_data_sets(
            benchmark.test_set_ids, DataSet, reference_data_sets
        )
        test_set_collection = DataSetCollection(data_sets=test_sets)

        with open("test-set-collection.json", "w") as file:
            file.write(test_set_collection.json())

    @classmethod
    def _retrieve_results(cls, benchmark: Benchmark):
        """Retrieves the full results for a benchmark.

        Parameters
        ----------
        benchmark
            The benchmark to retrieve the results for.
        """

        results = BenchmarkResult.from_rest(
            project_id=benchmark.project_id,
            study_id=benchmark.study_id,
            model_id=benchmark.id,
        )

        output_directory = "analysis"
        os.makedirs(output_directory, exist_ok=True)

        with open(
            os.path.join(output_directory, "benchmark-results.json"), "w"
        ) as file:
            file.write(results.json())

    @classmethod
    def _generate(
        cls,
        model: Benchmark,
        conda_environment,
        max_time,
        evaluator_preset,
        evaluator_port,
        n_evaluator_workers,
        include_results,
        reference_data_sets: Optional[List[Union[DataSet, QCDataSet]]],
        optimization_result: Optional[OptimizationResult],
    ):

        from openff.evaluator.client import RequestOptions

        super(BenchmarkInputFactory, cls)._generate(
            model=model,
            conda_environment=conda_environment,
            max_time=max_time,
            evaluator_preset=evaluator_preset,
            evaluator_port=evaluator_port,
            n_evaluator_workers=n_evaluator_workers,
            include_results=include_results,
            reference_data_sets=reference_data_sets,
            optimization_result=optimization_result,
        )

        # Save the benchmark definition in the directory
        benchmark_path = "benchmark.json"

        with open(benchmark_path, "w") as file:
            file.write(model.json())

        # Retrieve the force field.
        cls._retrieve_force_field(model, optimization_result)

        # Retrieve the data sets.
        cls._retrieve_data_sets(model, reference_data_sets)

        # Create an Evaluator server configuration
        evaluator_configuration = cls._generate_evaluator_config(
            preset_name=evaluator_preset,
            conda_environment=conda_environment,
            n_workers=n_evaluator_workers,
            port=evaluator_port,
        )

        with open("server-config.json", "w") as file:
            file.write(evaluator_configuration.json())

        # Create a job submission file
        cls._generate_submission_script(
            "bench",
            conda_environment,
            evaluator_preset,
            max_time,
            [
                "nonbonded benchmark run --restart true",
                "nonbonded benchmark analyze",
            ],
        )

        # Generate a set of request options
        request_options = RequestOptions()
        request_options.calculation_layers = ["SimulationLayer"]
        request_options.json("estimation-options.json", format=True)

        # Optionally retrieve any previously generated results.
        if include_results:
            cls._retrieve_results(model)
