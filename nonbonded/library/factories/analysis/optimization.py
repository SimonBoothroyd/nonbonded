import errno
import logging
import os
from collections import defaultdict
from glob import glob
from typing import Optional

from nonbonded.library.factories.analysis import AnalysisFactory
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import (
    DataSetResult,
    EvaluatorTargetResult,
    OptimizationResult,
    RechargeTargetResult,
)
from nonbonded.library.models.targets import EvaluatorTarget, RechargeTarget
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.library.utilities.migration import reindex_results

logger = logging.getLogger(__name__)


class OptimizationFactory(AnalysisFactory):
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
    def _analyze_evaluator_target(
        cls,
        optimization: Optimization,
        target: EvaluatorTarget,
        target_directory: str,
        reindex: bool,
    ) -> Optional[EvaluatorTargetResult]:

        from openff.evaluator.client import RequestResult

        results_path = os.path.join(target_directory, "results.json")

        if not os.path.isfile(results_path):
            return None

        # Load the reference data set
        reference_data_set = DataSetCollection.parse_file(
            os.path.join("targets", target.id, "training-set-collection.json")
        )

        results = RequestResult.from_json(results_path)

        if reindex:
            results = reindex_results(results, reference_data_set)

        estimated_data_set = results.estimated_properties

        # Generate statistics about each iteration.
        data_set_result = DataSetResult.from_evaluator(
            reference_data_set=reference_data_set,
            estimated_data_set=estimated_data_set,
            analysis_environments=optimization.analysis_environments,
            statistic_types=[StatisticType.RMSE],
        )

        objective_function = cls._read_objective_function(target_directory)

        return EvaluatorTargetResult(
            objective_function=target.weight * objective_function,
            statistic_entries=data_set_result.statistic_entries,
        )

    @classmethod
    def _analyze_recharge_target(
        cls,
        target: EvaluatorTarget,
        target_directory: str,
    ) -> Optional[RechargeTargetResult]:

        objective_function = cls._read_objective_function(target_directory)

        return RechargeTargetResult(
            objective_function=target.weight * objective_function,
        )

    @classmethod
    def generate(cls, model, reindex):

        from openforcefield.typing.engines.smirnoff import ForceField as OFFForceField

        # Load in the definition of the optimization to optimize.
        optimization = Optimization.parse_file("optimization.json")

        # Create directories to store the results in
        output_directory = "analysis"
        os.makedirs(output_directory, exist_ok=True)

        for target in optimization.targets:
            os.makedirs(os.path.join(output_directory, target.id))

        # Load in the refit force field (if it exists)
        refit_force_field_path = os.path.join(
            "result", "optimize", "force-field.offxml"
        )

        if not os.path.isfile(refit_force_field_path):

            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), refit_force_field_path
            )

        refit_force_field_off = OFFForceField(
            refit_force_field_path, allow_cosmetic_attributes=True
        )
        refit_force_field = ForceField.from_openff(refit_force_field_off)

        # Determine the number of optimization iterations.
        n_iterations = len(
            glob(
                os.path.join(
                    "optimize.tmp", optimization.targets[0].id, "iter_*", "results.json"
                )
            )
        )

        if n_iterations == 0:
            raise ValueError(
                "No iteration results could be found, even though a refit force field "
                "was. Make sure not to delete the `optimize.tmp` directory after the "
                "optimization has completed."
            )

        # Analyse the results of each iteration.
        target_results = defaultdict(dict)

        for iteration in range(n_iterations):

            logger.info(f"Analysing the results of iteration {iteration}")

            for target in optimization.targets:

                logger.info(f"Analysing the {target.id} target.")

                iteration_directory = os.path.join(
                    "optimize.tmp", target.id, "iter_" + str(iteration).zfill(4)
                )

                # Analyse the target
                if isinstance(target, EvaluatorTarget):
                    target_result = cls._analyze_evaluator_target(
                        optimization, target, iteration_directory, reindex
                    )
                elif isinstance(target, RechargeTarget):
                    target_result = cls._analyze_recharge_target(
                        target, iteration_directory
                    )
                else:
                    raise NotImplementedError()

                if target_result is None:

                    raise RuntimeError(
                        f"The results of the {target.id} target could not be "
                        f"found for iteration {iteration}."
                    )

                target_results[iteration][target.id] = target_result

                # Save the result
                with open(
                    os.path.join(
                        output_directory, target.id, f"iteration-{iteration}.json"
                    ),
                    "w",
                ) as file:
                    file.write(target_result.json())

        # Save the full results
        optimization_results = OptimizationResult(
            project_id=optimization.project_id,
            study_id=optimization.study_id,
            id=optimization.id,
            target_results=target_results,
            refit_force_field=refit_force_field,
        )

        with open(
            os.path.join(output_directory, "optimization-results.json"), "w"
        ) as file:
            file.write(optimization_results.json())
