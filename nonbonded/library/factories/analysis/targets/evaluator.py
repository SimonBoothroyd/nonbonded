import logging
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

_logger = logging.getLogger(__name__)


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
        reference_data_set: PhysicalPropertyDataSet = PhysicalPropertyDataSet.from_json(
            os.path.join(target_directory, "training-set.json")
        )

        # Check to see if any of the ids were set to strings that can't be cast to
        # integers, and if so, apply slight re-indexing
        try:
            {int(entry.id) for entry in reference_data_set.properties}
        except (TypeError, ValueError):

            _logger.warning(
                "The reference data set contains properties with ids that cannot be "
                "cast to integers - attempting to fix. Note this in general is not "
                "recommended and in future it is suggested to use integer ids in "
                "physical property data sets."
            )

            for i, physical_property in enumerate(reference_data_set):
                physical_property.id = str(i + 1)

            reindex = True

        reference_data_set: DataSet = DataSet.from_pandas(
            reference_data_set.to_pandas(),
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
