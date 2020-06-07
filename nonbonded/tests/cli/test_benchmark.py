import pytest

from nonbonded.cli.benchmark import benchmark as benchmark_cli
from nonbonded.library.models.datasets import DataSet
from nonbonded.library.models.projects import Benchmark
from nonbonded.tests.backend.crud.utilities.create import (
    create_benchmark,
    create_data_set,
)


@pytest.mark.usefixtures("change_api_url")
class TestBenchmarkCLI:
    @classmethod
    def _mock_get_benchmark(cls, requests_mock, benchmark: Benchmark):
        requests_mock.get(
            Benchmark._get_endpoint(
                project_id=benchmark.project_id,
                study_id=benchmark.study_id,
                benchmark_id=benchmark.id,
            ),
            text=benchmark.json(),
        )

    @classmethod
    def _mock_get_data_set(cls, requests_mock, data_set: DataSet):
        requests_mock.get(
            DataSet._get_endpoint(data_set_id=data_set.id), text=data_set.json(),
        )

    @pytest.mark.parametrize("output_to_file", [True, False])
    def test_retrieve(self, output_to_file, requests_mock, runner):

        benchmark = create_benchmark(
            "project-1", "study-1", "benchmark-1", ["data-set-1"], None, "openff-1.0.0"
        )
        self._mock_get_benchmark(requests_mock, benchmark)

        arguments = [
            "retrieve",
            "--project-id",
            benchmark.project_id,
            "--study-id",
            benchmark.study_id,
            "--benchmark-id",
            benchmark.id,
        ]

        if output_to_file:
            arguments.extend(["--output", "benchmark.json"])

        result = runner.invoke(benchmark_cli, arguments)
        assert result.exit_code == 0

        if output_to_file:
            with open("benchmark.json") as file:
                assert file.read().replace("\n", "") == benchmark.json()
        else:
            assert result.output.replace("\n", "") == benchmark.json()

    def test_generate(self, requests_mock, runner):

        benchmark = create_benchmark(
            "project-1",
            "study-1",
            "benchmark-1",
            ["data-set-1"],
            None,
            "openff-1.0.0.offxml",
        )
        self._mock_get_benchmark(requests_mock, benchmark)
        self._mock_get_data_set(requests_mock, create_data_set("data-set-1"))

        arguments = [
            "generate",
            "--project-id",
            benchmark.project_id,
            "--study-id",
            benchmark.study_id,
            "--benchmark-id",
            benchmark.id,
            "--max-workers",
            1,
        ]

        result = runner.invoke(benchmark_cli, arguments)
        assert result.exit_code == 0
