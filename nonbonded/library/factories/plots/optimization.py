import logging
import os
from typing import List

from typing_extensions import Literal

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
    def _load_sub_study(cls, directory):

        optimization = Optimization.parse_file(
            os.path.join(directory, "optimization.json")
        )

        optimization_result = OptimizationResult.parse_file(
            os.path.join(directory, "analysis", "optimization-results.json")
        )

        return optimization, optimization_result

    @classmethod
    def _plot(
        cls,
        directories: List[str],
        sub_studies: List[Optimization],
        results: List[OptimizationResult],
        file_type: Literal["png", "pdf"],
    ):

        # Plot the percentage change in the final vs initial parameters.
        plot_parameter_changes(
            sub_studies,
            results,
            "absolute",
            False,
            "",
            file_type,
        )

        # Plot the objective function per iteration
        plot_objective_per_iteration(
            sub_studies,
            results,
            True,
            "",
            file_type,
        )

        # Plot the change in RMSE of the training data.
        for optimization, result in zip(sub_studies, results):

            os.makedirs(optimization.id, exist_ok=True)

            plot_rmse_change(result, optimization.id, file_type)
