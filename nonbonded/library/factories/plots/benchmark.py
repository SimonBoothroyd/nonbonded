import logging
import os

from nonbonded.library.factories.plots import PlotFactory
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.plotting.benchmark import plot_results

logger = logging.getLogger(__name__)


class BenchmarkPlotFactory(PlotFactory):
    @classmethod
    def plot(cls):

        # Load in the benchmark and the results.
        benchmark = Benchmark.parse_file("benchmark.json")

        benchmark_result = BenchmarkResult.parse_file(
            os.path.join("analysis", "benchmark-results.json")
        )

        # Load in the benchmarked data sets
        reference_data_sets = DataSetCollection.parse_file("test-set-collection.json")

        # Create an output directory
        output_directory = "plots"
        os.makedirs(output_directory, exist_ok=True)

        # Plot the results
        plot_results(
            benchmarks=[benchmark],
            benchmark_results=[benchmark_result],
            data_sets=reference_data_sets.data_sets,
            output_directory=output_directory,
        )
