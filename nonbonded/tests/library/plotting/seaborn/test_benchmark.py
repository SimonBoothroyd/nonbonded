import os

import pytest
from typing_extensions import Literal

from nonbonded.library.plotting.seaborn.benchmark import (
    plot_categorized_rmse,
    plot_overall_statistics,
    plot_scatter_results,
)
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.tests.utilities.factory import create_data_set


@pytest.mark.parametrize("file_type", ["png", "pdf"])
def test_plot_overall_statistics(
    benchmarks_and_results,
    file_type: Literal["png", "pdf"],
    tmpdir,
):

    benchmarks, results, _ = benchmarks_and_results

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

    benchmarks, results, _ = benchmarks_and_results

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

    benchmarks, results, _ = benchmarks_and_results

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
