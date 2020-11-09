"""A module which aids in producing plots of benchmarking data with plots."""
from collections import defaultdict
from typing import Dict, List

import numpy

from nonbonded.library.models.datasets import DataSet
from nonbonded.library.models.plotly import (
    ErrorBar,
    Figure,
    Legend,
    MarkerStyle,
    ScatterTrace,
    Subplot,
)
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.plotting.plotly.utilities import unique_colors
from nonbonded.library.plotting.utilities import (
    combine_data_set_results,
    property_type_to_title,
)
from nonbonded.library.statistics.statistics import StatisticType


def plot_overall_statistics(
    benchmarks: List[Benchmark],
    benchmark_results: List[BenchmarkResult],
    statistic_type: StatisticType,
) -> Figure:
    """Plots an overview of how each benchmark performed against each type of property
    included in the training set.

    Parameters
    ----------
    benchmarks
        The benchmarks which have been performed.
    benchmark_results
        The analyzed outputs of the benchmarks.
    statistic_type
        The type of statistic to plot.
    """

    property_traces = defaultdict(list)

    colors = [f"rgb{color}" for color in unique_colors(len(benchmarks))]

    for benchmark, benchmark_result, color in zip(
        benchmarks, benchmark_results, colors
    ):

        show_legend = True

        for statistic in benchmark_result.data_set_result.statistic_entries:

            if (
                statistic.statistic_type != statistic_type
                or statistic.category is not None
            ):
                continue

            data_type = property_type_to_title(
                statistic.property_type, statistic.n_components
            )

            property_traces[data_type].append(
                ScatterTrace(
                    name=benchmark.name,
                    x=[benchmark.name],
                    y=[statistic.value],
                    error_y=ErrorBar(
                        symmetric=False,
                        array=[numpy.abs(statistic.upper_95_ci - statistic.value)],
                        arrayminus=[numpy.abs(statistic.lower_95_ci - statistic.value)],
                    ),
                    marker=MarkerStyle(color=color, symbol="circle-open"),
                    legendgroup=benchmark.name,
                    showlegend=show_legend,
                    hoverinfo="name",
                )
            )

            show_legend = False

    return Figure(
        subplots=[
            Subplot(
                title=property_type,
                show_x_ticks=False,
                y_axis_label=statistic_type.value,
                traces=[*traces],
            )
            for property_type, traces in property_traces.items()
        ],
        legend=Legend(),
    )


def plot_scatter_results(
    benchmarks: List[Benchmark],
    benchmark_results: List[BenchmarkResult],
    data_sets: List[DataSet],
) -> Dict[str, Figure]:
    """Plots the estimated value of each benchmarks property against the reference
    value.

    Parameters
    ----------
    benchmarks
        The benchmarks which have been performed.
    benchmark_results
        The analyzed outputs of the benchmarks.
    data_sets
        The reference data sets benchmarked against.
    """

    # Re-shape the data into a pandas data frame for easier manipulation.
    results_frame = combine_data_set_results(data_sets, benchmarks, benchmark_results)

    if len(results_frame) == 0:
        return {}

    # Define a 'unique' color per category
    all_categories = [*results_frame["Category"].unique()]
    colors = [f"rgb{color}" for color in unique_colors(10)]

    category_colors = {
        category: colors[i % 10] for i, category in enumerate(all_categories)
    }

    # Build one figure per property type.
    figures = {}

    for property_type in results_frame["Property Title"].unique():

        property_data = results_frame[results_frame["Property Title"] == property_type]

        subplots = []
        show_legend = {category: True for category in all_categories}

        for benchmark in benchmarks:

            benchmark_data = property_data[
                property_data["Benchmark Id"] == benchmark.id
            ]

            if len(benchmark_data) == 0:
                continue

            categories = [*benchmark_data["Category"].unique()]

            traces = []

            for category in categories:

                category_data = benchmark_data[benchmark_data["Category"] == category]

                traces.append(
                    ScatterTrace(
                        name=category,
                        x=[*category_data["Estimated Value"]],
                        y=[*category_data["Reference Value"]],
                        error_x=ErrorBar(
                            symmetric=True,
                            array=[*category_data["Estimated Std"]],
                            arrayminus=None,
                        ),
                        error_y=ErrorBar(
                            symmetric=True,
                            array=[*category_data["Reference Std"]],
                            arrayminus=None,
                        ),
                        marker=MarkerStyle(color=category_colors[category]),
                        legendgroup=category,
                        showlegend=show_legend[category],
                    )
                )

                show_legend[category] = False

            subplots.append(
                Subplot(
                    title=benchmark.name,
                    x_axis_label="Estimated",
                    y_axis_label="Reference",
                    traces=traces,
                )
            )

        figures[property_type] = Figure(
            subplots=subplots,
            legend=Legend(orientation="v"),
            shared_axes=True,
        )

    return figures
