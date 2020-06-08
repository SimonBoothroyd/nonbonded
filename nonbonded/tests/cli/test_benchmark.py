import pytest
from openforcefield.typing.engines.smirnoff.forcefield import (
    ForceField as SMIRNOFFForceField,
)

from nonbonded.cli.benchmark import benchmark as benchmark_cli
from nonbonded.library.models.forcefield import ForceField
from nonbonded.tests.backend.crud.utilities.create import (
    create_benchmark,
    create_benchmark_result,
    create_data_set,
    create_empty_study,
    create_force_field,
    create_optimization,
)
from nonbonded.tests.cli.utilities import (
    mock_get_benchmark,
    mock_get_benchmark_result,
    mock_get_data_set,
    mock_get_study,
)


@pytest.mark.usefixtures("change_api_url")
class TestBenchmarkCLI:
    def test_retrieve(self, requests_mock, runner):

        benchmark = create_benchmark(
            "project-1",
            "study-1",
            "benchmark-1",
            ["data-set-1"],
            None,
            create_force_field(),
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
            ForceField.from_openff(SMIRNOFFForceField("openff-1.0.0.offxml")),
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
            create_force_field(),
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

    def test_list(self, requests_mock, runner):

        study = create_empty_study("project-1", "study-1")
        study.optimizations = [
            create_optimization("project-1", "study-1", "optimization-1", [" "])
        ]
        study.benchmarks = [
            create_benchmark(
                "project-1", "study-1", "benchmark-1", [" "], "optimization-1", None
            )
        ]
        mock_get_study(requests_mock, study)

        result = runner.invoke(
            benchmark_cli,
            ["list", "--project-id", "project-1", "--study-id", "study-1"],
        )

        if result.exit_code != 0:
            raise result.exception

        assert study.benchmarks[0].id in result.output
