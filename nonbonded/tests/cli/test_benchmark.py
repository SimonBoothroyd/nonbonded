import pytest

from nonbonded.cli.benchmark import benchmark as benchmark_cli
from nonbonded.tests.backend.crud.utilities.create import (
    create_benchmark,
    create_benchmark_result,
    create_data_set,
)
from nonbonded.tests.cli.utilities import (
    mock_get_benchmark,
    mock_get_benchmark_result,
    mock_get_data_set,
)


@pytest.mark.usefixtures("change_api_url")
class TestBenchmarkCLI:
    def test_retrieve(self, requests_mock, runner):

        benchmark = create_benchmark(
            "project-1", "study-1", "benchmark-1", ["data-set-1"], None, "openff-1.0.0"
        )
        mock_get_benchmark(requests_mock, benchmark)

        arguments = [
            "retrieve",
            "--project-id",
            benchmark.project_id,
            "--study-id",
            benchmark.study_id,
            "--benchmark-id",
            benchmark.id,
        ]

        result = runner.invoke(benchmark_cli, arguments)

        if result.exit_code != 0:
            raise result.exception

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
        mock_get_benchmark(requests_mock, benchmark)
        mock_get_data_set(requests_mock, create_data_set("data-set-1"))

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

        if result.exit_code != 0:
            raise result.exception

    def test_results(self, requests_mock, runner):

        benchmark = create_benchmark(
            "project-1",
            "study-1",
            "benchmark-1",
            ["data-set-1"],
            None,
            "openff-1.0.0.offxml",
        )
        data_set = create_data_set("data-set-1")
        data_set.entries[0].id = 1
        benchmark_result = create_benchmark_result(
            "project-1", "study-1", "benchmark-1", data_set,
        )

        mock_get_data_set(requests_mock, data_set)
        mock_get_benchmark(requests_mock, benchmark)
        mock_get_benchmark_result(requests_mock, benchmark_result)

        arguments = [
            "results",
            "--project-id",
            benchmark.project_id,
            "--study-id",
            benchmark.study_id,
            "--benchmark-id",
            benchmark.id,
        ]

        result = runner.invoke(benchmark_cli, arguments)

        if result.exit_code != 0:
            raise result.exception
