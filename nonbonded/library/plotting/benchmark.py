import os
import re
import warnings
from typing import Dict, List

import numpy
from typing_extensions import Literal

from nonbonded.library.models.datasets import DataSet, DataSetEntry
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.plotting.utilities import plot_scatter, property_type_to_title
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.library.utilities.string import camel_to_kebab_case


def plot_overall_statistics(
    benchmarks: List[Benchmark],
    benchmark_results: List[BenchmarkResult],
    statistic_type: StatisticType,
    output_directory: str,
    file_type: Literal["png", "pdf"] = "png",
):
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
    output_directory
        The directory in which to save the plot.
    file_type
        The file type to use for the plots.
    """
    import pandas
    import seaborn
    from matplotlib import pyplot

    benchmark_names = sorted(benchmark.name for benchmark in benchmarks)

    plot_data = pandas.DataFrame(
        [
            {
                "Name": benchmark.name,
                "Data Type": property_type_to_title(
                    statistic.property_type, statistic.n_components
                ),
                "Value": statistic.value,
                "Lower CI": numpy.abs(statistic.lower_95_ci - statistic.value),
                "Upper CI": numpy.abs(statistic.upper_95_ci - statistic.value),
            }
            for benchmark, benchmark_result in zip(benchmarks, benchmark_results)
            for statistic in benchmark_result.data_set_result.statistic_entries
            if statistic.statistic_type == statistic_type and statistic.category is None
        ]
    )

    # Extract the unique data types (e.g. property types).
    data_types = sorted(plot_data["Data Type"].unique())

    # Create the plot.
    plot = seaborn.FacetGrid(
        data=plot_data,
        col="Data Type",
        hue="Name",
        sharey=False,
        height=4.0,
        aspect=0.5 + len(data_types) * 0.05,
        col_order=data_types,
    )

    for data_index, data_type in enumerate(data_types):

        type_plot_data = plot_data[plot_data["Data Type"] == data_type]
        axis = plot.facet_axis(0, data_index)

        # Plot the error bars and marker for each benchmark.
        for index, benchmark_name in enumerate(benchmark_names):

            benchmark_plot_data = type_plot_data[
                type_plot_data["Name"] == benchmark_name
            ]

            axis.errorbar(
                index,
                benchmark_plot_data["Value"],
                yerr=[
                    benchmark_plot_data["Lower CI"],
                    benchmark_plot_data["Upper CI"],
                ],
                label=benchmark_name,
                capsize=5.0,
                capthick=1.5,
                linestyle="none",
                marker="o",
                markersize=10.0,
                markerfacecolor="none",
                color=seaborn.color_palette(n_colors=1)[0],
            )

        # Add axis names
        axis.set_xticks(range(0, len(benchmark_names)))
        axis.set_xticklabels(benchmark_names, rotation=90)
        axis.set_xlim(-0.5, len(benchmark_names) - 0.5)

        if data_index == 0:
            axis.set_ylabel(f"${statistic_type.value}$")

    statistic_name = re.sub(r"[\W_]+", "", statistic_type.value).lower()

    # Set the column titles
    plot.set_titles("{col_name}")

    # Save the figure.
    plot.savefig(
        os.path.join(
            output_directory,
            f"overall-{statistic_name}.{file_type}",
        ),
        bbox_inches="tight",
    )
    pyplot.close(plot.fig)


def plot_categorized_rmse(
    benchmarks: List[Benchmark],
    benchmark_results: List[BenchmarkResult],
    output_directory: str,
    file_type: Literal["png", "pdf"] = "png",
):
    """Plots the RMSE in each benchmarked property partitioned by the assigned
    statistics category.

    Parameters
    ----------
    benchmarks
        The benchmarks which have been performed.
    benchmark_results
        The analyzed outputs of the benchmarks.
    output_directory
        The directory in which to save the plots.
    file_type
        The file type to use for the plots.
    """
    import pandas
    import seaborn
    from matplotlib import pyplot

    # Reshape the statistics into a uniform data frame.
    data_rows = [
        {
            "Data Type": f"{statistic.property_type}-{statistic.n_components}",
            "Name": benchmark.name,
            "Value": statistic.value,
            "Lower CI": numpy.abs(statistic.lower_95_ci - statistic.value),
            "Upper CI": numpy.abs(statistic.upper_95_ci - statistic.value),
            "Category": statistic.category,
        }
        for benchmark, result in zip(benchmarks, benchmark_results)
        for statistic in result.data_set_result.statistic_entries
        if statistic.statistic_type == StatisticType.RMSE
        and statistic.category is not None
    ]

    plot_data = pandas.DataFrame(data_rows)

    # Extract the unique data types (e.g. property types) which will be plotted
    # in separate figures.
    data_types = plot_data["Data Type"].unique()

    os.makedirs(os.path.join(output_directory, "categorized-rmse"), exist_ok=True)

    for data_type in data_types:

        # Extract a data frame containing only the data type which should
        # be included in this figure.
        type_plot_data = plot_data[plot_data["Data Type"] == data_type]

        def category_sort_key(category_string: str):

            splitter = (
                "<"
                if "<" in category_string
                else "~"
                if "~" in category_string
                else ">"
                if ">" in category_string
                else None
            )

            if splitter is None:
                return category_string, None, None

            splitter_ordering = {"<": 0, "~": 1, ">": 2}
            split_string = category_string.split(splitter)

            return (
                split_string[0].strip(),
                split_string[1].strip(),
                splitter_ordering[splitter],
            )

        categories = sorted(
            type_plot_data["Category"].unique(), key=category_sort_key, reverse=True
        )
        category_indices = [x * 2 for x in range(1, len(categories) + 1)]

        n_categories = len(categories)

        with seaborn.axes_style("white"):

            figure, axis = pyplot.subplots(figsize=(5.0, 1.5 + (0.5 * n_categories)))

            shifts = numpy.linspace(-0.5, 0.5, len(benchmarks))

            # Plot the data for each benchmark.
            for index, benchmark in enumerate(benchmarks):

                benchmark_plot_data = type_plot_data[
                    type_plot_data["Name"] == benchmark.name
                ]

                # Plot the error bars and with the circle marker on top.
                axis.barh(
                    benchmark_plot_data["Category"]
                    .replace(categories, category_indices)
                    .values
                    - shifts[index],
                    benchmark_plot_data["Value"],
                    xerr=[
                        benchmark_plot_data["Lower CI"],
                        benchmark_plot_data["Upper CI"],
                    ],
                    height=1.0 / (len(benchmarks) - 1),
                    label=benchmark.name,
                )

            # Add a simple legend.
            axis.legend()

            # Add title and axis names
            axis.set_yticks(category_indices)
            axis.set_yticklabels(categories)

            axis.set_xlim(left=0.0)
            axis.set_ylim(0.5, (len(categories) + 1) * 2.0 - 0.5)

            axis.set_xlabel("RMSE")

        # Save the figure.
        figure.savefig(
            os.path.join(
                output_directory,
                "categorized-rmse",
                f"{camel_to_kebab_case(data_type)}.{file_type}",
            ),
            bbox_inches="tight",
        )
        pyplot.close(figure)


def plot_scatter_results(
    benchmarks: List[Benchmark],
    benchmark_results: List[BenchmarkResult],
    data_sets: List[DataSet],
    output_directory: str,
    file_type: Literal["png", "pdf"] = "png",
    highlight_categories: List[str] = None,
):
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
    output_directory
        The directory in which to save the plots.
    file_type
        The file type to use for the plots.
    highlight_categories
        Particular categories (e.g. ``"Alcohol > Ester"``) to highlight on the plot.
        If ``None`` all points will be colored the same. If an empty list then each
        category will be colored separately.
    """
    import pandas
    import seaborn
    from matplotlib import pyplot

    reference_data_points: Dict[int, DataSetEntry] = {
        entry.id: entry for data_set in data_sets for entry in data_set.entries
    }

    # Re-shape the data into a pandas data frame for easier plotting.
    data_rows = []

    for benchmark, benchmark_result in zip(benchmarks, benchmark_results):

        for result_entry in benchmark_result.data_set_result.result_entries:

            reference_data_point = reference_data_points[result_entry.reference_id]

            reference_value = reference_data_point.value
            reference_std = reference_data_point.std_error

            estimated_value = result_entry.estimated_value
            estimated_std = result_entry.estimated_std_error

            # For now trim down the number of different categories and
            # shorten certain category names.
            category = re.sub("[<>~]", "+", result_entry.category).replace(
                "Carboxylic Acid Ester", "Ester"
            )

            # Handle the highlighting of particular categories if requested.
            if highlight_categories is None or (
                len(highlight_categories) != 0 and category not in highlight_categories
            ):
                category = "None"

            property_type = (
                f"{reference_data_point.property_type}-"
                f"{len(reference_data_point.components)}"
            )

            # Generate a meaningful title for the plot.
            property_title = property_type_to_title(
                reference_data_point.property_type, len(reference_data_point.components)
            )

            data_row = {
                "Benchmark Id": benchmark.name,
                "Property Type": property_type,
                "Property Title": property_title,
                "Estimated Value": estimated_value,
                "Estimated Std": estimated_std,
                "Reference Value": reference_value,
                "Reference Std": reference_std,
                "Category": category,
            }
            data_rows.append(data_row)

    results_frame = pandas.DataFrame(data_rows)

    # Determine the unique categories and property types in the plot.
    categories = ["None", *sorted({*results_frame["Category"].unique()} - {"None"})]
    property_types = results_frame["Property Type"].unique()

    # Choose a colorblind friendly palette.
    palette = seaborn.color_palette("colorblind", n_colors=len(categories))

    # Grey out any non-highlighted points if a particular set of categories should
    # be highlighted.
    if highlight_categories is not None:

        palette.pop(0)
        palette.insert(0, (0.6, 0.6, 0.6, 0.2))

    # Plot each property type separately.
    os.makedirs(os.path.join(output_directory, "scatter-plots"), exist_ok=True)

    for property_type in property_types:

        plot_frame = results_frame[results_frame["Property Type"] == property_type]

        # Catch seaborn warnings about numpy nan masks.
        with warnings.catch_warnings():

            warnings.simplefilter("ignore", UserWarning)

            plot = seaborn.FacetGrid(
                plot_frame,
                col="Benchmark Id",
                sharex="row",
                sharey="row",
                hue_order=categories,
                palette=palette,
                height=4.0,
                aspect=0.8,
            )
            plot.map_dataframe(
                plot_scatter,
                "Estimated Value",
                "Reference Value",
                "Reference Std",
                "Estimated Std",
                "Category",
                categories,
                color=palette,
                marker="o",
                linestyle="None",
            )

            min_limit = numpy.min(
                [
                    numpy.minimum(axis.get_xlim(), axis.get_ylim())
                    for axis in plot.axes.ravel()
                ]
            )
            max_limit = numpy.max(
                [
                    numpy.maximum(axis.get_xlim(), axis.get_ylim())
                    for axis in plot.axes.ravel()
                ]
            )

            for axis in plot.axes.ravel():

                axis.set_xlim(min_limit, max_limit)
                axis.set_ylim(min_limit, max_limit)

        # Add a legend showing only the highlighted categories.
        plot_categories = sorted(
            x for x in plot_frame["Category"].unique() if x != "None"
        )
        plot.add_legend(label_order=plot_categories)

        # Add a title to each sub-plot.
        plot.set_titles("{col_name}")
        pyplot.subplots_adjust(top=0.85)

        # Give the full plot a title.
        property_title = plot_frame["Property Title"].unique()[0]
        plot.fig.suptitle(property_title)

        plot.savefig(
            os.path.join(
                output_directory,
                "scatter-plots",
                f"{camel_to_kebab_case(property_type)}.{file_type}",
            )
        )
