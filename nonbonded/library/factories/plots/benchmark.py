import logging
import os
from typing import List

from typing_extensions import Literal

from nonbonded.library.factories.plots import PlotFactory
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.plotting.seaborn.benchmark import (
    plot_categorized_rmse,
    plot_overall_statistics,
    plot_scatter_results,
)
from nonbonded.library.statistics.statistics import StatisticType

logger = logging.getLogger(__name__)


class BenchmarkPlotFactory(PlotFactory):
    @classmethod
    def _load_sub_study(cls, directory):

        benchmark = Benchmark.parse_file(os.path.join(directory, "benchmark.json"))
        benchmark_result = BenchmarkResult.parse_file(
            os.path.join(directory, "analysis", "benchmark-results.json")
        )

        return benchmark, benchmark_result

    @classmethod
    def _plot(
        cls,
        directories: List[str],
        sub_studies: List[Benchmark],
        results: List[BenchmarkResult],
        file_type: Literal["png", "pdf"],
    ):

        data_sets = {}

        # Load in the benchmarked data sets
        for directory in directories:

            reference_data_sets = DataSetCollection.parse_file(
                os.path.join(directory, "test-set-collection.json")
            )

            data_sets.update(
                {data_set.id: data_set for data_set in reference_data_sets.data_sets}
            )

        # Plot overall statistics about the optimization.
        for statistic_type in [StatisticType.RMSE, StatisticType.R2]:
            plot_overall_statistics(sub_studies, results, statistic_type, "", file_type)

        # Plot statistics about each category
        plot_categorized_rmse(sub_studies, results, "", file_type)

        # Plot the results as a scatter plot.
        plot_scatter_results(sub_studies, results, [*data_sets.values()], "", file_type)
