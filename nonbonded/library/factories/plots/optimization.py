import logging
import os

from nonbonded.library.factories.plots import PlotFactory
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.plotting.optimization import plot_results

logger = logging.getLogger(__name__)


class OptimizationFactory(PlotFactory):
    @classmethod
    def generate(cls, model):

        # Load in the optimization and the results.
        optimization_result = OptimizationResult.parse_file(
            os.path.join("analysis", "optimization-results.json")
        )

        # Create an output directory
        output_directory = "plots"
        os.makedirs(output_directory, exist_ok=True)

        # Plot the results
        plot_results(
            optimizations=[model],
            optimization_results=[optimization_result],
            output_directory=output_directory,
        )
