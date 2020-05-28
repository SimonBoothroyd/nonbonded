import os
from collections import defaultdict
from typing import List

from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.plotting.utilities import (
    plot_categories,
    plot_categories_with_custom_ci,
    property_type_to_title,
)


def _plot_parameter_changes(
    optimizations: List[Optimization],
    optimization_results: List[OptimizationResult],
    output_directory: str,
):
    import pandas
    import seaborn

    from simtk import unit as simtk_unit

    parameter_attributes = ["epsilon", "rmin_half"]
    default_units = {
        "epsilon": simtk_unit.kilocalories_per_mole,
        "rmin_half": simtk_unit.angstrom,
    }

    # Find the values of the original and optimized parameters.
    data_rows = []

    for optimization, optimization_result in zip(optimizations, optimization_results):

        original_force_field = optimization.initial_force_field.to_openff()
        optimized_force_field = optimization_result.refit_force_field.to_openff()

        original_handler = original_force_field.get_parameter_handler("vdW")
        optimized_handler = optimized_force_field.get_parameter_handler("vdW")

        retrained_smirks = [
            parameter.smirks for parameter in optimization.parameters_to_train
        ]

        for parameter in original_handler.parameters:

            if parameter.smirks not in retrained_smirks:
                continue

            for attribute_type in parameter_attributes:

                original_value = getattr(parameter, attribute_type)
                optimized_value = getattr(
                    optimized_handler.parameters[parameter.smirks], attribute_type
                )

                percentage_change = (
                    (optimized_value - original_value) / original_value * 100.0
                )

                absolute_change = (optimized_value - original_value).value_in_unit(
                    default_units[attribute_type]
                )

                data_row = {
                    "Name": optimization.name,
                    "Smirks": parameter.smirks,
                    "Attribute": f"{attribute_type} ({default_units[attribute_type]})",
                    "Absolute Parameter Change": absolute_change,
                    "% Parameter Change": percentage_change,
                }

                data_rows.append(data_row)

    parameter_data = pandas.DataFrame(data_rows)

    palette = seaborn.color_palette(n_colors=len(optimizations))

    for header in ["% Parameter Change", "Absolute Parameter Change"]:

        print(header)
        print(parameter_data)

        plot = seaborn.FacetGrid(
            parameter_data, row="Attribute", height=4.0, aspect=2.0, sharey=False
        )
        plot.map_dataframe(plot_categories, "Smirks", header, "Name", color=palette)

        plot.add_legend()

        plot.savefig(os.path.join(output_directory, f"{header}.png"))


def _plot_objective_per_iteration(
    optimizations: List[Optimization],
    optimization_results: List[OptimizationResult],
    output_directory: str,
):
    import pandas
    import seaborn
    from matplotlib import pyplot

    data_rows = []

    for optimization, optimization_result in zip(optimizations, optimization_results):

        for iteration, value in optimization_result.objective_function.items():
            data_rows.append(
                {
                    "Name": optimization.name,
                    "Iteration": iteration,
                    "Objective Function": value,
                }
            )

    objective_function = pandas.DataFrame(data_rows)

    plot = seaborn.FacetGrid(
        objective_function,
        col="Name",
        size=4.0,
        aspect=1.0,
        sharex=False,
        sharey=False,
    )
    plot.map(pyplot.plot, "Iteration", "Objective Function")
    plot.set_titles("{col_name}")

    plot.savefig(os.path.join(output_directory, "Objective Function.png"))


def _plot_relative_rmse(
    optimization_result: OptimizationResult,
    output_directory: str,
    categorical: bool = True,
):
    import pandas
    import seaborn
    from matplotlib import pyplot

    if not categorical:
        raise NotImplementedError()

    if 0 not in optimization_result.statistics:

        raise ValueError(
            "The optimization results must contain the statistics for iteration "
            "0 to plot the relative RMSE values."
        )

    iterations = sorted(optimization_result.statistics)
    iterations = [iterations[1], iterations[-1]]

    # Gather the initial statistics
    initial_statistics = defaultdict(dict)

    for statistic in optimization_result.statistics[0]:

        property_type = f"{statistic.property_type} {statistic.n_components}"
        initial_statistics[property_type][statistic.category] = statistic

    # Convert the statistics into a data frame.
    data_rows = []

    for iteration, statistics in optimization_result.statistics.items():

        if iteration not in iterations:
            continue

        statistics = [
            statistic
            for statistic in statistics
            if (statistic.category is None and not categorical)
            or (statistic.category is not None and categorical)
        ]

        for statistic in statistics:

            property_type = f"{statistic.property_type} {statistic.n_components}"

            property_title = property_type_to_title(
                statistic.property_type, statistic.n_components
            )

            initial_value = initial_statistics[property_type][statistic.category].value

            data_row = {
                "Iteration": iteration,
                "Property Type": property_type,
                "Property Title": property_title,
                "Value": statistic.value - initial_value,
                "Lower 95% CI": statistic.value - statistic.lower_95_ci,
                "Upper 95% CI": statistic.upper_95_ci - statistic.value,
                "Category": statistic.category,
            }

            data_rows.append(data_row)

    results_frame = pandas.DataFrame(data_rows)

    categories = sorted(results_frame["Category"].unique())
    property_types = results_frame["Property Type"].unique()

    palette = seaborn.color_palette(n_colors=len(categories))

    for property_type in property_types:

        plot_frame = results_frame[results_frame["Property Type"] == property_type]

        plot = seaborn.FacetGrid(
            plot_frame, size=4.0, aspect=0.6 * len(iterations), sharey=False,
        )
        plot.map_dataframe(
            plot_categories_with_custom_ci,
            "Iteration",
            "Value",
            "Category",
            "Lower 95% CI",
            "Upper 95% CI",
            color=palette,
        )

        # plot.set_titles("RMSE_n - RMSE_0|{row_name}")
        #
        # for i, axes_row in enumerate(plot.axes):
        #
        #     for j, axes_col in enumerate(axes_row):
        #
        #         row, col = axes_col.get_title().split("|")
        #
        #         axes_col.set_title(col.strip())
        #
        #         if j == 0:
        #             axes_col.set_ylabel(f"{row.strip()}")

        plot.add_legend()

        pyplot.subplots_adjust(top=0.85)

        property_title = plot_frame["Property Title"].unique()[0]
        plot.fig.suptitle(property_title)

        plot.savefig(
            os.path.join(output_directory, f"{property_type} Relative RMSE.png")
        )


def plot_results(
    optimizations: List[Optimization],
    optimization_results: List[OptimizationResult],
    output_directory: str,
):

    # Plot the percentage change in the final vs initial parameters.
    _plot_parameter_changes(optimizations, optimization_results, output_directory)

    # Plot the objective function per iteration
    _plot_objective_per_iteration(optimizations, optimization_results, output_directory)

    # Plot the change in RMSE of the training data.
    if len(optimizations) == 1:
        _plot_relative_rmse(optimization_results[0], output_directory)
