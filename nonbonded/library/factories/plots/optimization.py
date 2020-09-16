import logging
import os

from nonbonded.library.factories.plots import PlotFactory
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.plotting.optimization import (
    plot_objective_per_iteration,
    plot_parameter_changes,
    plot_rmse_change,
)

logger = logging.getLogger(__name__)


class OptimizationPlotFactory(PlotFactory):
    @classmethod
    def plot(cls):

        # Load in the optimization and the results.
        optimization = Optimization.parse_file("optimization.json")

        optimization_result = OptimizationResult.parse_file(
            os.path.join("analysis", "optimization-results.json")
        )

        # Create an output directory
        output_directory = "plots"
        os.makedirs(output_directory, exist_ok=True)

        # Plot the percentage change in the final vs initial parameters.
        plot_parameter_changes(
            [optimization],
            [optimization_result],
            "absolute",
            False,
            output_directory,
            "pdf",
        )

        # Plot the objective function per iteration
        plot_objective_per_iteration(
            [optimization],
            [optimization_result],
            True,
            output_directory,
            "pdf",
        )

        # Plot the change in RMSE of the training data.
        plot_rmse_change(optimization_result, output_directory, "pdf")
