import os
from typing import Optional

from nonbonded.library.factories.analysis.targets import TargetAnalysisFactory
from nonbonded.library.models.authors import Author
from nonbonded.library.models.datasets import DataSet
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import DataSetResult, EvaluatorTargetResult
from nonbonded.library.models.targets import EvaluatorTarget
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.library.utilities.migration import reindex_results


class EvaluatorAnalysisFactory(TargetAnalysisFactory):
    @classmethod
    def analyze(
        cls,
        optimization: Optimization,
        target: EvaluatorTarget,
        target_directory: str,
        result_directory: str,
        reindex: bool = False,
    ) -> Optional[EvaluatorTargetResult]:

        from openff.evaluator.client import RequestResult
        from openff.evaluator.datasets import PhysicalPropertyDataSet

        results_path = os.path.join(result_directory, "results.json")

        if not os.path.isfile(results_path):
            return None

        # Load the reference data set
        reference_data_set = DataSet.from_pandas(
            PhysicalPropertyDataSet.from_json(
                os.path.join(target_directory, "training-set.json")
            ).to_pandas(),
            identifier="empty",
            description="empty",
            authors=[Author(name="empty", email="email@email.com", institute="empty")],
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

        objective_function = cls._read_objective_function(result_directory)

        return EvaluatorTargetResult(
            objective_function=target.weight * objective_function,
            statistic_entries=data_set_result.statistic_entries,
        )
