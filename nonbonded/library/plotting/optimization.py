import os
from collections import defaultdict
from typing import TYPE_CHECKING, List

import numpy
from typing_extensions import Literal

from nonbonded.library.models.forcefield import Parameter
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import (
    DataSetStatistic,
    OptimizationResult,
    TargetResultType,
)
from nonbonded.library.plotting.utilities import plot_categories
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.library.utilities.string import camel_to_kebab_case

if TYPE_CHECKING:
    import simtk.unit
    from openforcefield.typing.engines.smirnoff.forcefield import (
        ForceField as OFFForceField,
    )


def _default_parameter_unit(parameter: Parameter) -> "simtk.unit":
    """Returns the default unit for a parameter.

    Parameters
    ----------
    parameter
        The parameter to retrieve the unit of.

    Returns
    -------
        The default parameter unit.
    """

    import simtk.unit

    default_units = {
        "epsilon": simtk.unit.kilocalories_per_mole,
        "rmin_half": simtk.unit.angstrom,
        "sigma": simtk.unit.angstrom,
        "charge_increment1": simtk.unit.elementary_charge,
    }

    return default_units[parameter.attribute_name]


def _extract_parameter_value(
    force_field: "OFFForceField", parameter: Parameter
) -> float:
    """Extracts the value of a parameter from a force field object
    in its default unit.

    Parameters
    ----------
    force_field
        The force field which contains the parameter.
    parameter
        The parameter to extract the value of

    Returns
    -------
        The value of the parameter.
    """

    handler = force_field.get_parameter_handler(parameter.handler_type)
    off_parameter = handler.parameters[parameter.smirks]

    value = getattr(off_parameter, parameter.attribute_name)

    return value.value_in_unit(_default_parameter_unit(parameter))


def plot_parameter_changes(
    optimizations: List[Optimization],
    optimization_results: List[OptimizationResult],
    mode: Literal["percent", "absolute"],
    show_legend: bool,
    output_directory: str,
    file_type: Literal["png", "pdf"] = "png",
):
    """Plots the change in the force field parameters which have been trained over
    the course of an optimization.

    Parameters
    ----------
    optimizations
        The optimizations which have been performed.
    optimization_results
        The analyzed outputs of the optimizations.
    mode
        The type of change to plot. This may either be absolute changes
        or percent changes.
    show_legend
        Whether to show the legend.
    output_directory
        The directory in which to save the plots.
    file_type
        The file type to use for the plots.
    """
    import pandas
    import seaborn
    from matplotlib import pyplot

    # Determine which parameters were refit
    parameters = defaultdict(dict)

    for index, (optimization, optimization_result) in enumerate(
        zip(optimizations, optimization_results)
    ):

        original_force_field = optimization.force_field.to_openff()
        refit_force_field = optimization_result.refit_force_field.to_openff()

        for parameter in optimization.parameters_to_train:

            parameters[parameter][index] = (
                _extract_parameter_value(original_force_field, parameter),
                _extract_parameter_value(refit_force_field, parameter),
            )

    # Re-shape the parameter values into a plottable pandas frame.
    data_rows = []

    for parameter in parameters:
        for optimization_index in parameters[parameter]:

            original_value, refit_value = parameters[parameter][optimization_index]

            percentage_change = (refit_value - original_value) / original_value * 100.0
            absolute_change = refit_value - original_value

            unit = _default_parameter_unit(parameter).get_symbol()

            data_row = {
                "Name": optimizations[optimization_index].name,
                "Handler": parameter.handler_type,
                "SMIRKS": parameter.smirks,
                "Attribute": f"{parameter.attribute_name} ({unit})",
                r"$\Delta$": absolute_change,
                r"% $\Delta$": percentage_change,
            }

            data_rows.append(data_row)

    # Plot the data.
    parameter_data = pandas.DataFrame(data_rows)
    palette = seaborn.color_palette(n_colors=len(optimizations))

    header = r"$\Delta$" if mode == "absolute" else r"% $\Delta$"
    handlers = {*parameter_data["Handler"].unique()}

    for handler in handlers:

        handler_data = parameter_data[parameter_data["Handler"] == handler]

        n_attributes = len(handler_data["Attribute"].unique())
        n_smirks = len(handler_data["SMIRKS"].unique())

        plot = seaborn.FacetGrid(
            handler_data,
            row="Attribute",
            height=1.5 * n_attributes,
            aspect=1.0 + 0.1 * (n_smirks - 1),
            sharey=False,
        )
        plot.map_dataframe(plot_categories, "SMIRKS", header, "Name", color=palette)
        plot.set_titles("{row_name}")

        for index in range(n_attributes):

            # Move the x-axis to y = 0
            plot.axes[index, 0].spines["bottom"].set_position(("data", 0.0))
            # Remove the x-axis tick marks.
            plot.axes[index, 0].tick_params(axis="x", which="both", length=0)

        # Move the x-axis labels back under the plot, rather than on the x axis.
        pyplot.setp(
            plot.axes[n_attributes - 1, 0].get_xticklabels(),
            transform=plot.axes[n_attributes - 1, 0].get_xaxis_transform(),
            rotation=90,
        )

        if show_legend:
            plot.add_legend()

        handler_name = camel_to_kebab_case(handler.replace("vdW", "vdw"))

        plot.savefig(
            os.path.join(output_directory, f"{handler_name}-{mode}-change.{file_type}")
        )
        pyplot.close(plot.fig)


def plot_objective_per_iteration(
    optimizations: List[Optimization],
    optimization_results: List[OptimizationResult],
    show_legend: bool,
    output_directory: str,
    file_type: Literal["png", "pdf"] = "png",
):
    """Plots the objective function for each optimizations target as a function of the
    optimization iteration.

    Different optimization are coloured separately while different targets are styled
    with different markers.

    Parameters
    ----------
    optimizations
        The optimizations which have been performed.
    optimization_results
        The analyzed outputs of the optimizations.
    show_legend
        Whether to show the legend.
    output_directory
        The directory in which to save the plots.
    file_type
        The file type to use for the plots.
    """

    import pandas
    import seaborn
    from matplotlib import pyplot

    data_rows = []

    for optimization, optimization_result in zip(optimizations, optimization_results):
        for iteration, iteration_result in optimization_result.target_results.items():
            for target_id, target_result in iteration_result.items():

                data_rows.append(
                    {
                        "Optimization": optimization.name,
                        "Target": target_id,
                        "Iteration": iteration,
                        "Objective Function": target_result.objective_function,
                    }
                )

    plot_data = pandas.DataFrame(data_rows)

    hue = "Optimization" if len(plot_data["Optimization"].unique()) > 1 else None
    style = "Target" if len(plot_data["Target"].unique()) > 1 else None

    plot = seaborn.relplot(
        data=plot_data,
        x="Iteration",
        y="Objective Function",
        hue=hue,
        style=style,
        height=4.0,
        legend="full" if show_legend else False,
    )

    plot.savefig(os.path.join(output_directory, f"objective-function.{file_type}"))
    pyplot.close(plot.fig)


def _plot_target_rmse_change(
    target_id: str,
    initial_result: TargetResultType,
    final_result: TargetResultType,
    output_directory: str,
    file_type: Literal["png", "pdf"] = "png",
):
    import pandas
    import seaborn
    from matplotlib import pyplot

    def statistic_to_key(statistic):

        return (
            f"{statistic.property_type}-{statistic.n_components}"
            if isinstance(statistic, DataSetStatistic)
            else None
        )

    # Gather the initial statistics
    initial_statistics = {
        (statistic_to_key(statistic), statistic.category): statistic
        for statistic in initial_result.statistic_entries
        if statistic.category is not None
        and statistic.statistic_type == StatisticType.RMSE
    }
    final_statistics = {
        (statistic_to_key(statistic), statistic.category): statistic
        for statistic in final_result.statistic_entries
        if statistic.category is not None
        and statistic.statistic_type == StatisticType.RMSE
    }

    assert {*initial_statistics} == {*final_statistics}

    # Reshape the statistics into a uniform data frame.
    data_rows = []

    for statistic_key in initial_statistics:

        initial_statistic = initial_statistics[statistic_key]
        final_statistic = final_statistics[statistic_key]

        data_type, category = statistic_key

        data_row = {
            "Data Type": data_type,
            "Initial Value": initial_statistic.value,
            "Initial Lower CI": numpy.abs(
                initial_statistic.lower_95_ci - initial_statistic.value
            ),
            "Initial Upper CI": numpy.abs(
                initial_statistic.upper_95_ci - initial_statistic.value
            ),
            "Final Value": final_statistic.value,
            "Final Lower CI": numpy.abs(
                final_statistic.lower_95_ci - final_statistic.value
            ),
            "Final Upper CI": numpy.abs(
                final_statistic.upper_95_ci - final_statistic.value
            ),
            "Category": category,
        }

        data_rows.append(data_row)

    plot_data = pandas.DataFrame(data_rows)

    # Extract the unique data types (e.g. property types) which will be plotted
    # in separate figures.
    data_types = plot_data["Data Type"].unique()

    for data_type in data_types:

        # Extract a data frame containing only the data type which should
        # be included in this figure.
        type_plot_data = plot_data[plot_data["Data Type"] == data_type]
        n_categories = len(type_plot_data["Category"].unique())

        with seaborn.axes_style("white"):

            figure, axis = pyplot.subplots(figsize=(5.0, 1.5 + (0.5 * n_categories)))

            # Plot the error bars and then plot the RMSE circle marker on top.
            axis.errorbar(
                type_plot_data["Initial Value"],
                type_plot_data.index,
                xerr=[
                    type_plot_data["Initial Lower CI"],
                    type_plot_data["Initial Upper CI"],
                ],
                color="skyblue",
                capsize=5.0,
                capthick=1.5,
                linestyle="none",
            )
            axis.errorbar(
                type_plot_data["Final Value"],
                type_plot_data.index,
                xerr=[
                    type_plot_data["Final Lower CI"],
                    type_plot_data["Final Upper CI"],
                ],
                color="limegreen",
                capsize=5.0,
                capthick=1.5,
                linestyle="none",
            )
            axis.scatter(
                type_plot_data["Initial Value"],
                type_plot_data.index,
                color="skyblue",
                label="Initial",
            )
            axis.scatter(
                type_plot_data["Final Value"],
                type_plot_data.index,
                color="limegreen",
                label="Final",
            )

            # Add a simple legend.
            axis.legend()

            # Add title and axis names
            axis.set_yticks(type_plot_data.index)
            axis.set_yticklabels(type_plot_data["Category"])

            axis.set_xlim(left=0.0)
            axis.set_xlabel("RMSE")

        data_name = "-" if data_type is None else f"-{camel_to_kebab_case(data_type)}-"

        # Save the figure.
        figure.savefig(
            os.path.join(
                output_directory,
                f"{target_id}{data_name}rmse.{file_type}",
            ),
            bbox_inches="tight",
        )
        pyplot.close(figure)


def plot_rmse_change(
    optimization_result: OptimizationResult,
    output_directory: str,
    file_type: Literal["png", "pdf"] = "png",
):
    """Plots the change in the RMSE between the first and the last iteration of an
    optimization for each optimization target.

    Parameters
    ----------
    optimization_result
        The analyzed outputs of the optimization.
    output_directory
        The directory in which to save the plots.
    file_type
        The file type to use for the plots.
    """
    if 0 not in optimization_result.target_results:

        raise KeyError(
            "The optimization results must contain the statistics for iteration "
            "0 to plot the change in RMSE values."
        )

    if len(optimization_result.target_results) <= 1:

        raise KeyError(
            "The optimization results must contain the statistics for at least "
            "two iterations to plot the change in RMSE values."
        )

    final_iteration = sorted(optimization_result.target_results)[-1]

    for target_id, initial_result in optimization_result.target_results[0].items():

        final_result = optimization_result.target_results[final_iteration][target_id]

        _plot_target_rmse_change(
            target_id, initial_result, final_result, output_directory, file_type
        )
