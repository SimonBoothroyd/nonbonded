import json
from typing import Tuple

import numpy
import pytest
from forcebalance.nifty import lp_dump

from nonbonded.library.factories.analysis.targets.recharge import (
    RechargeAnalysisFactory,
)
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.targets import RechargeTarget
from nonbonded.library.utilities import temporary_cd
from nonbonded.library.utilities.environments import ChemicalEnvironment
from nonbonded.tests.utilities.factory import (
    create_optimization,
    create_recharge_target,
)


@pytest.fixture()
def mock_target(tmpdir) -> Tuple[Optimization, RechargeTarget, str]:
    """Create a mock recharge target directory which is populated with a dummy
    set of results.

    Returns
    -------
        A tuple of the parent optimization, the mock target and the path to the
        directory in which the files were created.
    """

    with temporary_cd(str(tmpdir)):

        # Mock the target to analyze.
        target = create_recharge_target("recharge-target-1", ["qc-data-set-1"])

        optimization = create_optimization(
            "project-1", "study-1", "optimization-1", [target]
        )
        optimization.analysis_environments = [
            ChemicalEnvironment.Alkane,
            ChemicalEnvironment.Alcohol,
        ]

        # Create a dummy set of residuals.
        with open("residuals.json", "w") as file:
            json.dump({"C": 9.0, "CO": 4.0}, file)

        lp_dump({"X": 1.0}, "objective.p")

    return optimization, target, str(tmpdir)


def test_analyze(mock_target):

    optimization, target, directory = mock_target

    # Analyze the mocked results
    target_result = RechargeAnalysisFactory.analyze(
        optimization=optimization,
        target=target,
        target_directory=directory,
        result_directory=directory,
    )

    assert numpy.isclose(target_result.objective_function, 1.0)
    assert len(target_result.statistic_entries) == 3

    statistic_per_category = {
        statistic.category: statistic.value
        for statistic in target_result.statistic_entries
    }

    assert numpy.isclose(statistic_per_category["Alkane"], 3.0)
    assert numpy.isclose(statistic_per_category["Alcohol"], 2.0)

    assert numpy.isclose(statistic_per_category[None], numpy.sqrt(13.0 / 2.0))


def test_analyze_recharge_target_missing(mock_target):

    optimization, target, directory = mock_target

    assert (
        RechargeAnalysisFactory.analyze(
            optimization=optimization,
            target=target,
            target_directory="",
            result_directory="",
        )
        is None
    )
