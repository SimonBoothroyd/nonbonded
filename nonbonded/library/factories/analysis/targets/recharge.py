import json
import os
from collections import defaultdict
from typing import Optional

from nonbonded.library.factories.analysis.targets import TargetAnalysisFactory
from nonbonded.library.models.datasets import Component
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import RechargeTargetResult, Statistic
from nonbonded.library.models.targets import RechargeTarget
from nonbonded.library.statistics.statistics import StatisticType, bootstrap_residuals
from nonbonded.library.utilities.checkmol import components_to_categories


class RechargeAnalysisFactory(TargetAnalysisFactory):
    @classmethod
    def analyze(
        cls,
        optimization: Optimization,
        target: RechargeTarget,
        target_directory: str,
        result_directory: str,
    ) -> Optional[RechargeTargetResult]:

        residuals_path = os.path.join(result_directory, "residuals.json")

        if not os.path.isfile(residuals_path):
            return None

        # Load in the residuals
        with open(residuals_path) as file:
            squared_residuals = json.load(file)

        # Categorize the smiles
        smiles_per_category = defaultdict(list)

        smiles_per_category[None] = [*squared_residuals]

        for smiles in squared_residuals:

            categories = components_to_categories(
                [Component(smiles=smiles, mole_fraction=0.0, exact_amount=1)],
                optimization.analysis_environments,
            )

            for category in categories:
                smiles_per_category[category].append(smiles)

        # Compute RMSE statistics for this target.
        statistic_entries = []

        for category in smiles_per_category:

            category_residuals = [
                squared_residuals[smiles] for smiles in smiles_per_category[category]
            ]

            rmse, rmse_std, rmse_ci = bootstrap_residuals(category_residuals)

            statistic_entry = Statistic(
                statistic_type=StatisticType.RMSE,
                category=category,
                value=rmse,
                lower_95_ci=rmse_ci[0],
                upper_95_ci=rmse_ci[1],
            )
            statistic_entries.append(statistic_entry)

        objective_function = cls._read_objective_function(result_directory)

        return RechargeTargetResult(
            objective_function=target.weight * objective_function,
            statistic_entries=statistic_entries,
        )
