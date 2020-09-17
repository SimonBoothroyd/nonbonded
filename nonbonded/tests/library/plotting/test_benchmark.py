import os
from typing import List, Tuple

import pytest
from typing_extensions import Literal

from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.plotting.benchmark import (
    plot_categorized_rmse,
    plot_overall_statistics,
    plot_scatter_results,
)
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_benchmark_result,
    create_data_set,
)


@pytest.fixture()
def benchmarks_and_results(
    force_field: ForceField,
) -> Tuple[List[Benchmark], List[BenchmarkResult]]:

    benchmarks = []
    benchmark_results = []

    for index in range(2):

        benchmark = create_benchmark(
            "project-1",
            "study-1",
            f"benchmark-{index + 1}",
            ["data-set-1"],
            None,
            force_field,
        )
        benchmark.name = f"Benchmark {index + 1}"
        benchmarks.append(benchmark)

        benchmark_result = create_benchmark_result(
            "project-1", "study-1", "benchmark-1", [create_data_set("data-set-1", 1)]
        )

        for statistic_entry in benchmark_result.data_set_result.statistic_entries:
            statistic_entry.value /= index + 1
            statistic_entry.lower_95_ci /= index + 1
            statistic_entry.upper_95_ci /= index + 1

        benchmark_results.append(benchmark_result)

    return benchmarks, benchmark_results


@pytest.mark.parametrize("file_type", ["png", "pdf"])
def test_plot_overall_statistics(
    benchmarks_and_results,
    file_type: Literal["png", "pdf"],
    tmpdir,
):

    benchmarks, results = benchmarks_and_results

    plot_overall_statistics(
        benchmarks,
        results,
        StatisticType.RMSE,
        tmpdir,
        file_type,
    )

    assert os.path.isfile(os.path.join(tmpdir, f"overall-rmse.{file_type}"))


@pytest.mark.parametrize("file_type", ["png", "pdf"])
def test_plot_categorized_rmse(
    benchmarks_and_results,
    file_type: Literal["png", "pdf"],
    tmpdir,
):

    benchmarks, results = benchmarks_and_results

    plot_categorized_rmse(
        benchmarks,
        results,
        tmpdir,
        file_type,
    )

    assert os.path.isfile(
        os.path.join(tmpdir, "categorized-rmse", f"density-2.{file_type}")
    )


@pytest.mark.parametrize("file_type", ["png", "pdf"])
def test_plot_scatter_results(
    benchmarks_and_results,
    file_type: Literal["png", "pdf"],
    tmpdir,
):

    benchmarks, results = benchmarks_and_results

    plot_scatter_results(
        benchmarks,
        results,
        [create_data_set("data-set-1", 1)],
        tmpdir,
        file_type,
    )

    assert os.path.isfile(
        os.path.join(tmpdir, "scatter-plots", f"density-2.{file_type}")
    )
