from collections import defaultdict

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
    optimization: Optimization,
    optimization_result: OptimizationResult,
) -> Figure:
    """Plots the objective function for each optimizations target as a function of the
    optimization iteration.

    Different optimization are coloured separately while different targets are styled
    with different markers.

    Parameters
    ----------
    optimization
        The optimization which has been performed.
    optimization_result
        The analyzed output of the optimization.
    """

    target_iterations = defaultdict(dict)

    for iteration, iteration_result in optimization_result.target_results.items():
        for target_id, target_result in iteration_result.items():

            target_iterations[target_id][iteration] = target_result.objective_function

    color = f"rgb{unique_colors(1)[0]}"
    markers = unique_markers(len(optimization.targets))

    traces = [
        ScatterTrace(
            name=target_id,
            x=[str(x) for x in iterations],
            y=[iterations[x] for x in iterations],
            marker=MarkerStyle(color=color, symbol=markers[i]),
            legendgroup=target_id,
            showlegend=True,
            mode="lines+markers",
        )
        for i, (target_id, iterations) in enumerate(target_iterations.items())
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
