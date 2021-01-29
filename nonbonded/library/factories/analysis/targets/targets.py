import abc
import os
from typing import Optional

from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import TargetResult
from nonbonded.library.models.targets import OptimizationTarget


class TargetAnalysisFactory(abc.ABC):
    @classmethod
    def _read_objective_function(cls, target_directory) -> float:
        """Reads the value of the objective function from a ForceBalance
        nifty file stored in an iteration output directory

        Parameters
        ----------
        target_directory
            The directory which contains the nifty file.

        Returns
        -------
            The value of the objective function.
        """

        from forcebalance.nifty import lp_load

        # Extract the value of this iterations objective function
        objective_file_path = os.path.join(target_directory, "objective.p")
        objective_statistics = lp_load(objective_file_path)

        return objective_statistics["X"]

    @classmethod
    @abc.abstractmethod
    def analyze(
        cls,
        optimization: Optimization,
        target: OptimizationTarget,
        target_directory: str,
        result_directory: str,
    ) -> Optional[TargetResult]:

        raise NotImplementedError()
