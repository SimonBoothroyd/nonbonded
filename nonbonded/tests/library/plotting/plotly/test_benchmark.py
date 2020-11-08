from plotly.io import write_json

from nonbonded.library.plotting.plotly.benchmark import (
    plot_overall_statistics,
    plot_scatter_results,
)
from nonbonded.library.statistics.statistics import StatisticType


def test_plot_overall_statistics(benchmarks_and_results, tmpdir):

    benchmarks, results, _ = benchmarks_and_results

    figure = plot_overall_statistics(benchmarks, results, StatisticType.RMSE)

    assert figure is not None
    assert figure.to_plotly() is not None


def test_plot_scatter_results(benchmarks_and_results, tmpdir):

    benchmarks, results, data_sets = benchmarks_and_results

    figures = plot_scatter_results(benchmarks, results, data_sets)

    for figure in figures.values():

        assert figure is not None
        assert figure.to_plotly() is not None
