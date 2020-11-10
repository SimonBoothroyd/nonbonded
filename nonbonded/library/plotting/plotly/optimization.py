from collections import defaultdict
from typing import List, Optional

from nonbonded.library.models.plotly import (
    Figure,
    Legend,
    MarkerStyle,
    ScatterTrace,
    Subplot,
)
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.plotting.plotly.utilities import unique_colors, unique_markers


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
