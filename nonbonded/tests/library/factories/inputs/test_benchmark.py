import os

import pytest
from openff.evaluator.forcefield import TLeapForceFieldSource

from nonbonded.library.factories.inputs.benchmark import BenchmarkInputFactory
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_benchmark_result,
    create_data_set,
    create_optimization_result,
)
from nonbonded.tests.utilities.mock import (
    mock_get_benchmark_result,
    mock_get_data_set,
    mock_get_optimization_result,
)


@pytest.fixture()
def benchmark(force_field) -> Benchmark:

    return create_benchmark(
        "project-1",
        "study-1",
        "benchmark-1",
        data_set_ids=["data-set-1"],
        optimization_id=None,
        force_field=force_field,
    )


@pytest.mark.usefixtures("change_api_url")
class TestBenchmarkInputFactory:
    @pytest.mark.parametrize(
        "force_field",
        [
            ForceField(
                inner_content=(
                    '<SMIRNOFF version="0.3" '
                    'aromaticity_model="OEAroModel_MDL"></SMIRNOFF>'
                )
            ),
            ForceField(inner_content=TLeapForceFieldSource().json()),
        ],
    )
    def test_retrieve_refit_force_field(self, force_field):

        benchmark = create_benchmark(
            "project-1",
            "study-1",
            "benchmark-1",
            data_set_ids=["data-set-1"],
            optimization_id=None,
            force_field=force_field,
        )

        is_smirnoff = "SMIRNOFF" in force_field.inner_content

        with temporary_cd():
            BenchmarkInputFactory._retrieve_force_field(benchmark)

            if is_smirnoff:
                assert os.path.isfile("force-field.offxml")
            else:
                assert os.path.isfile("force-field.json")

    def test_retrieve_force_field(self, requests_mock):

        # Mock a refit force field to retrieve.
        result = create_optimization_result(
            "project-1",
            "study-1",
            "optimization-1",
            ["evaluator-target-1"],
            [],
        )
        result.refit_force_field = ForceField(
            inner_content=(
                '<SMIRNOFF version="0.3" '
                'aromaticity_model="OEAroModel_MDL"></SMIRNOFF>'
            )
        )
        mock_get_optimization_result(requests_mock, result)

        # Mock a benchmark which targets the refit force field.
        benchmark = create_benchmark(
            "project-1",
            "study-1",
            "benchmark-1",
            data_set_ids=["data-set-1"],
            optimization_id="optimization-1",
            force_field=None,
        )

        with temporary_cd():

            BenchmarkInputFactory._retrieve_force_field(benchmark)
            assert os.path.isfile("force-field.offxml")

    def test_retrieve_data_sets(self, benchmark, requests_mock):

        # Mock the data set to retrieve.
        data_set = create_data_set("data-set-1", 1)
        mock_get_data_set(requests_mock, data_set)

        with temporary_cd():

            BenchmarkInputFactory._retrieve_data_sets(benchmark)

            assert os.path.isfile("test-set-collection.json")
            from nonbonded.library.models.datasets import DataSetCollection

            data_set_collection = DataSetCollection.parse_file(
                "test-set-collection.json"
            )
            assert data_set_collection.data_sets[0].json() == data_set.json()

    def test_retrieve_results(self, benchmark, requests_mock):

        result = create_benchmark_result(
            benchmark.project_id,
            benchmark.study_id,
            benchmark.id,
            create_data_set("data-set-1", 1),
        )
        mock_get_benchmark_result(requests_mock, result)

        with temporary_cd():

            BenchmarkInputFactory._retrieve_results(benchmark)

            stored_result = BenchmarkResult.parse_file(
                os.path.join("analysis", "benchmark-results.json")
            )
            assert stored_result.json() == result.json()

    def test_generate(self, benchmark, monkeypatch):

        # Mock the already tested functions
        monkeypatch.setattr(
            BenchmarkInputFactory, "_retrieve_force_field", lambda *args: None
        )
        monkeypatch.setattr(
            BenchmarkInputFactory, "_retrieve_data_sets", lambda *args: None
        )
        monkeypatch.setattr(
            BenchmarkInputFactory, "_generate_submission_script", lambda *args: None
        )
        monkeypatch.setattr(
            BenchmarkInputFactory, "_retrieve_results", lambda *args: None
        )

        with temporary_cd():

            BenchmarkInputFactory.generate(
                benchmark, "env", "01:00", "lilac-local", 8000, 1, True
            )
