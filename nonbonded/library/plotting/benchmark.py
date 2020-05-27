import os
from typing import Dict, List

import pandas
import seaborn
from matplotlib import pyplot

from nonbonded.library.models.datasets import DataSet, DataSetEntry
from nonbonded.library.models.projects import Benchmark
from nonbonded.library.models.results import BenchmarkResult
from nonbonded.library.plotting.utilities import plot_scatter, property_type_to_title

# def plot_statistic(statistic_types, output_directory):
#
#     statistic_types = [x.value for x in statistic_types]
#
#     summary_data_path = os.path.join("statistics", "all_statistics.csv")
#
#     summary_data = pandas.read_csv(summary_data_path)
#     summary_data = summary_data.sort_values("Study")
#     summary_data = summary_data[summary_data["Statistic"].isin(statistic_types)]
#
#     study_names = list(sorted({*summary_data["Study"]}))
#
#     palette = seaborn.color_palette(n_colors=len(study_names))
#
#     plot = seaborn.FacetGrid(
#         summary_data,
#         col="Property",
#         row="Statistic",
#         size=4.0,
#         aspect=1.0,
#         sharey=True,
#     )
#     plot.map_dataframe(
#         plot_bar_with_custom_ci,
#         f"Study",
#         f"Value",
#         f"Lower 95% CI",
#         f"Upper 95% CI",
#         color=palette,
#     )
#
#     plot.set_titles("{row_name}|{col_name}")
#
#     for i, axes_row in enumerate(plot.axes):
#
#         for j, axes_col in enumerate(axes_row):
#
#             row, col = axes_col.get_title().split("|")
#
#             if i == 0:
#                 axes_col.set_title(col.strip())
#             else:
#                 axes_col.set_title("")
#
#             if j == 0:
#                 axes_col.set_ylabel(f"${row.strip()}$")
#
#             axes_col.set_xticklabels([])
#
#     plot.add_legend()
#
#     plot.savefig(os.path.join(output_directory, "statistics.png"))
#
#
# def plot_statistic_per_environment(
#     property_types,
#     statistic_types,
#     output_directory,
#     per_composition=False,
#     reference_study=None
# ):
#
#     if per_composition:
#         per_environment_data_path = os.path.join("statistics", "per_composition.csv")
#     else:
#         per_environment_data_path = os.path.join("statistics", "per_environment.csv")
#
#     per_environment_data = pandas.read_csv(per_environment_data_path)
#
#     statistic_types = [x.value for x in statistic_types]
#
#     study_names = list(sorted({*per_environment_data["Study"]}))
#
#     for property_type, substance_type in property_types:
#
#         property_title = property_to_title(property_type, substance_type)
#
#         property_data = per_environment_data[
#             per_environment_data["Property"] == property_title
#         ]
#         property_data = property_data[property_data["Statistic"].isin(statistic_types)]
#
#         if reference_study is not None:
#
#             reference_data = property_data[property_data["Study"] == reference_study]
#             # property_data = property_data[property_data["Study"] != reference_study]
#
#             joined_data = pandas.merge(
#                 property_data,
#                 reference_data,
#                 on=["Property", "Statistic", "Environment"],
#                 suffixes=("", "_0"),
#             )
#
#             property_data = joined_data[joined_data["Value"] >= joined_data["Value_0"]]
#
#         palette = seaborn.color_palette(n_colors=len(study_names))
#
#         plot = seaborn.FacetGrid(
#             property_data,
#             col="Property",
#             row="Statistic",
#             height=4.0,
#             aspect=4.0,
#             sharey=False,
#         )
#         plot.map_dataframe(
#             plot_categories_with_custom_ci,
#             "Environment",
#             f"Value",
#             "Study",
#             f"Lower 95% CI",
#             f"Upper 95% CI",
#             color=palette,
#         )
#
#         plot.add_legend()
#
#         plot.set_titles("{row_name}|{col_name}")
#
#         for i, axes_row in enumerate(plot.axes):
#
#             for j, axes_col in enumerate(axes_row):
#
#                 row, col = axes_col.get_title().split("|")
#
#                 if i == 0:
#                     axes_col.set_title(col.strip())
#                 else:
#                     axes_col.set_title("")
#
#                 if j == 0:
#                     axes_col.set_ylabel(f"${row.strip()}$")
#
#         file_name = property_to_file_name(property_type, substance_type)
#
#         if reference_study is not None:
#             file_name = f"{file_name}_{reference_study}"
#
#         plot.savefig(
#             os.path.join(output_directory, f"{file_name}_statistics_per_env.png")
#         )


def plot_results(
    benchmarks: List[Benchmark],
    benchmark_results: List[BenchmarkResult],
    data_sets: List[DataSet],
    output_directory: str,
):

    reference_data_points: Dict[int, DataSetEntry] = {
        entry.id: entry for data_set in data_sets for entry in data_set.entries
    }

    # Refactor the data into a pandas data frame.
    data_rows = []

    for benchmark, benchmark_result in zip(benchmarks, benchmark_results):

        for results_entry in benchmark_result.analysed_result.results_entries:

            reference_data_point = reference_data_points[results_entry.reference_id]

            reference_value = reference_data_point.value
            reference_std = reference_data_point.std_error

            estimated_value = results_entry.estimated_value
            estimated_std = results_entry.estimated_std_error

            category = results_entry.category

            property_type = (
                f"{reference_data_point.property_type} "
                f"{len(reference_data_point.components)}"
            )

            property_title = property_type_to_title(
                reference_data_point.property_type, len(reference_data_point.components)
            )

            data_row = {
                "Benchmark Id": benchmark.id,
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

    categories = sorted(results_frame["Category"].unique())
    property_types = results_frame["Property Type"].unique()

    palette = seaborn.color_palette("Set1", len(categories))

    for property_type in property_types:

        plot_frame = results_frame[results_frame["Property Type"] == property_type]

        plot = seaborn.FacetGrid(
            plot_frame,
            col="Benchmark Id",
            sharex="row",
            sharey="row",
            hue_order=categories,
            palette=palette,
            size=4.0,
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

        plot.set_titles("{col_name}")
        plot.add_legend()

        pyplot.subplots_adjust(top=0.85)

        property_title = plot_frame["Property Title"].unique()[0]
        plot.fig.suptitle(property_title)

        plot.savefig(os.path.join(output_directory, f"{property_type}.png"))
