import os
import sys

from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_benchmark_result,
    create_data_set,
)


def test_plot(force_field, monkeypatch):

    from nonbonded.library.plotting.seaborn import benchmark as benchmark_module

    # Mock the required file inputs
    data_set = create_data_set("data-set-1", 1)
    data_set_collection = DataSetCollection(data_sets=[data_set])

    benchmark = create_benchmark(
        "project-1",
        "study-1",
        "benchmark-1",
        ["data-set-1"],
        None,
        force_field,
    )
    benchmark_result = create_benchmark_result(
        "project-1", "study-1", "benchmark-1", [create_data_set("data-set-1", 1)]
    )

    # Mock the already tested plotting methods.
    monkeypatch.setattr(benchmark_module, "plot_categorized_rmse", lambda *args: None)
    monkeypatch.setattr(benchmark_module, "plot_overall_statistics", lambda *args: None)
    monkeypatch.setattr(benchmark_module, "plot_scatter_results", lambda *args: None)

    if "nonbonded.library.factories.plots.benchmark" in sys.modules:
        sys.modules.pop("nonbonded.library.factories.plots.benchmark")

    from nonbonded.library.factories.plots.benchmark import BenchmarkPlotFactory

    with temporary_cd():

        # Save the inputs in their expected locations.
        data_set_collection.to_file("test-set-collection.json")
        benchmark.to_file("benchmark.json")
        os.makedirs("analysis")
        benchmark_result.to_file(os.path.join("analysis", "benchmark-results.json"))

        BenchmarkPlotFactory.plot([""], "png")

        assert os.path.isdir("plots")
