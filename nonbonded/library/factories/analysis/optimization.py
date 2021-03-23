import errno
import logging
import os
from collections import defaultdict
from glob import glob

from nonbonded.library.factories.analysis import AnalysisFactory
from nonbonded.library.factories.analysis.targets.evaluator import (
    EvaluatorAnalysisFactory,
)
from nonbonded.library.factories.analysis.targets.recharge import (
    RechargeAnalysisFactory,
)
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.models.targets import EvaluatorTarget, RechargeTarget
from nonbonded.library.utilities.provenance import summarise_current_versions

logger = logging.getLogger(__name__)

_TARGET_FACTORIES = {
    EvaluatorTarget: EvaluatorAnalysisFactory,
    RechargeTarget: RechargeAnalysisFactory,
}


class OptimizationAnalysisFactory(AnalysisFactory):
    @classmethod
    def _load_refit_force_field(cls) -> ForceField:
        """Load in the refit force field."""

        from openff.toolkit.typing.engines.smirnoff.forcefield import (
            ForceField as OFFForceField,
        )

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

        return refit_force_field

    @classmethod
    def analyze(cls, reindex):

        # Load in the definition of the optimization to optimize.
        optimization = Optimization.parse_file("optimization.json")

        # Create directories to store the results in
        output_directory = "analysis"
        os.makedirs(output_directory, exist_ok=True)

        for target in optimization.targets:
            os.makedirs(os.path.join(output_directory, target.id), exist_ok=True)

        # Load in the refit force field (if it exists)
        refit_force_field = cls._load_refit_force_field()

        # Determine the number of optimization iterations.
        target_n_iterations = [
            len(glob(os.path.join("optimize.tmp", target.id, "iter_*", "objective.p")))
            for target in optimization.targets
        ]

        n_iterations = min(target_n_iterations)

        if n_iterations == 0:
            raise RuntimeError(
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
                target_analyzer = _TARGET_FACTORIES.get(target.__class__, None)

                if target_analyzer is None:
                    raise NotImplementedError

                target_analyzer_kwargs = {}

                if isinstance(target_analyzer, EvaluatorAnalysisFactory):
                    target_analyzer_kwargs["reindex"] = reindex

                target_result = target_analyzer.analyze(
                    optimization,
                    target,
                    os.path.join("targets", target.id),
                    iteration_directory,
                    **target_analyzer_kwargs,
                )

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
            calculation_environment=cls._parse_calculation_environment(),
            analysis_environment=summarise_current_versions(),
            target_results=target_results,
            refit_force_field=refit_force_field,
        )

        with open(
            os.path.join(output_directory, "optimization-results.json"), "w"
        ) as file:
            file.write(optimization_results.json())
