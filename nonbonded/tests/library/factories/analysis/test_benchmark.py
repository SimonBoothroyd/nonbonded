import logging
import os

from nonbonded.library.factories.analysis.benchmark import BenchmarkAnalysisFactory
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.factory import create_benchmark, create_data_set


def test_benchmark_analysis(caplog, monkeypatch, dummy_conda_env):

    from openff.evaluator.client import RequestResult
    from openff.evaluator.datasets import PhysicalPropertyDataSet

    benchmark = create_benchmark(
        "project-1", "study-1", "benchmark-1", ["data-set-1"], "optimization-1", None
    )

    # Create a reference data set.
    reference_data_set = create_data_set("data-set-1")
    reference_data_set.entries.append(reference_data_set.entries[0].copy())
    reference_data_set.entries[0].id = 1
    reference_data_set.entries[1].id = 2

    # Create a set of evaluator results
    estimated_data_set = PhysicalPropertyDataSet()
    estimated_data_set.add_properties(reference_data_set.entries[0].to_evaluator())

    unsuccessful_properties = PhysicalPropertyDataSet()
    unsuccessful_properties.add_properties(reference_data_set.entries[1].to_evaluator())

    results = RequestResult()
    results.estimated_properties = estimated_data_set
    results.unsuccessful_properties = unsuccessful_properties

    with temporary_cd(os.path.dirname(dummy_conda_env)):

        # Save the expected input files.
        with open("benchmark.json", "w") as file:
            file.write(benchmark.json())

        with open("test-set-collection.json", "w") as file:
            file.write(DataSetCollection(data_sets=[reference_data_set]).json())

        results.json("results.json")

        with caplog.at_level(logging.WARNING):
            BenchmarkAnalysisFactory.analyze(True)

        assert (
            "1 properties could not be estimated and so were not analyzed"
            in caplog.text
        )

        assert os.path.isdir("analysis")
        assert os.path.isfile(os.path.join("analysis", "benchmark-results.json"))

        results_object = BenchmarkResult.parse_file(
            os.path.join("analysis", "benchmark-results.json")
        )
        assert len(results_object.calculation_environment) > 0
        assert len(results_object.analysis_environment) > 0
