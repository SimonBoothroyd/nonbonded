from collections import defaultdict
from typing import Dict, List, Optional

from nonbonded.library.models.plotly import (
    ErrorBar,
    Figure,
    Legend,
    MarkerStyle,
    ScatterTrace,
    Subplot,
)
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import OptimizationResult, TargetResultType
from nonbonded.library.models.targets import OptimizationTarget
from nonbonded.library.plotting.plotly.utilities import unique_colors, unique_markers
from nonbonded.library.plotting.utilities import combine_target_rmse


def plot_objective_per_iteration(
    optimizations: List[Optimization],
    optimization_results: List[Optional[OptimizationResult]],
) -> Figure:
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
    """

    target_iterations = defaultdict(lambda: defaultdict(dict))
    targets = set()

    for optimization, optimization_result in zip(optimizations, optimization_results):

        if optimization_result is None:
            continue

        for iteration, iteration_result in optimization_result.target_results.items():
            for target_id, target_result in iteration_result.items():

                target_iterations[optimization.id][target_id][
                    iteration
                ] = target_result.objective_function
                targets.add(target_id)

    targets = sorted(targets)

    colors = [f"rgb{color}" for color in unique_colors(10)]
    markers = unique_markers(11)

    def trace_name(optimization_id, target_id):

        if len(optimizations) <= 1:
            return target_id
        elif len(optimizations) > 1 and len(targets) <= 1:
            return optimization_id

        return f"{optimization_id}: {target_id}"

    traces = [
        ScatterTrace(
            name=trace_name(optimization_id, target_id),
            x=[str(x) for x in iterations],
            y=[iterations[x] for x in iterations],
            marker=MarkerStyle(
                color=colors[i % 10], symbol=markers[targets.index(target_id) % 11]
            ),
            legendgroup=trace_name(optimization_id, target_id),
            showlegend=True,
            mode="lines+markers",
            hoverinfo="none",
        )
        for i, optimization_id in enumerate(target_iterations)
        for target_id, iterations in target_iterations[optimization_id].items()
    ]

    return Figure(
        subplots=[
            Subplot(
                traces=traces,
                x_axis_label="Iteration",
                y_axis_label="Objective Function",
            )
        ],
        legend=Legend(orientation="h"),
    )


def plot_target_rmse(
    targets: List[OptimizationTarget],
    target_results: List[TargetResultType],
    target_labels: List[str],
) -> Dict[str, Figure]:
    """Plots the RMSE for each of the specified targets and for each data type
    contained within the target results.

    Parameters
    ----------
    targets
        The targets which the results were collected for.
    target_results
        The target results to plot.
    target_labels
        The label associated with each target result.
    """

    plot_data = combine_target_rmse(targets, target_results, target_labels)

    if len(plot_data) == 0:
        return {}

    # Extract the unique data types (e.g. property types) which will be plotted
    # in separate figures.
    data_types = plot_data["Data Type"].unique()

    # Select a set of colors for each label
    color_palette = (
        ["skyblue", "limegreen"] + []
        if len(target_labels) < 3
        else [f"rgb{color}" for color in unique_colors(10)]
    )
    colors = {label: color_palette[index] for index, label in enumerate(target_labels)}

    figures = {}

    for data_type in data_types:

        # Extract a data frame containing only the data type which should
        # be included in this figure.
        if data_type is not None:
            type_plot_data = plot_data[plot_data["Data Type"] == data_type]
        else:
            type_plot_data = plot_data[plot_data["Data Type"].isna()]

        # categories = sorted(
        #     type_plot_data["Category"].unique(), key=sort_categories_key, reverse=True
        # )

        labels = type_plot_data["Label"].unique()

        # Plot data for each label.
        traces = []

        for label in labels:

            label_plot_data = type_plot_data[type_plot_data["Label"] == label]

            traces.append(
                ScatterTrace(
                    name=label,
                    x=label_plot_data["Value"].to_list(),
                    y=label_plot_data["Category"].to_list(),
                    error_x=ErrorBar(
                        symmetric=False,
                        array=label_plot_data["Upper CI"].to_list(),
                        arrayminus=label_plot_data["Lower CI"].to_list(),
                    ),
                    marker=MarkerStyle(color=colors[label]),
                    legendgroup=label,
                    showlegend=True,
                    mode="markers",
                    hoverinfo="none",
                )
            )

        figures[data_type] = Figure(
            subplots=[Subplot(x_axis_label="RMSE", traces=traces)],
            legend=Legend(),
        )

    return figures
