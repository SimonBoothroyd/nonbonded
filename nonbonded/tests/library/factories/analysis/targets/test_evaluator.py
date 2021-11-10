import logging
import os.path
from typing import Tuple

import numpy
import pytest
from forcebalance.nifty import lp_dump
from openff.evaluator.client import RequestResult
from openff.evaluator.datasets import PhysicalPropertyDataSet

from nonbonded.library.factories.analysis.targets.evaluator import (
    EvaluatorAnalysisFactory,
)
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.targets import EvaluatorTarget
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.factory import (
    create_data_set,
    create_evaluator_target,
    create_optimization,
)


@pytest.fixture()
def mock_target(tmpdir) -> Tuple[Optimization, EvaluatorTarget, str]:
    """Create a mock evaluator target directory which is populated with a dummy
    set of results.

    Returns
    -------
        A tuple of the parent optimization, the mock target and the path to the
        directory in which the files were created.
    """

    with temporary_cd(str(tmpdir)):

        # Mock the target to analyze.
        target = create_evaluator_target("evaluator-target-1", ["data-set-1"])

        optimization = create_optimization(
            "project-1", "study-1", "optimization-1", [target]
        )
        optimization.analysis_environments = []

        # Create a dummy data set and estimated result.
        reference_data_set = create_data_set("data-set-1", 1)
        DataSetCollection(data_sets=[reference_data_set]).to_evaluator().json(
            "training-set.json"
        )

        results = RequestResult()
        results.estimated_properties = reference_data_set.to_evaluator()
        results.json("results.json")

        lp_dump({"X": 1.0}, "objective.p")

    return optimization, target, str(tmpdir)


def test_analyze(mock_target):

    optimization, target, directory = mock_target

    # Analyze the mocked results
    target_result = EvaluatorAnalysisFactory.analyze(
        optimization=optimization,
        target=target,
        target_directory=directory,
        result_directory=directory,
        reindex=True,
    )

    assert numpy.isclose(target_result.objective_function, 1.0)
    assert len(target_result.statistic_entries) == 1


def test_analyze_non_integer_ids(mock_target, caplog):

    optimization, target, directory = mock_target

    reference_data_set: PhysicalPropertyDataSet = PhysicalPropertyDataSet.from_json(
        os.path.join(directory, "training-set.json")
    )
    assert len(reference_data_set) == 1  # Sanity check in case this changes in future.
    reference_data_set.properties[0].id = "a"
    reference_data_set.json(os.path.join(directory, "training-set.json"))

    results = RequestResult()
    results.estimated_properties = reference_data_set
    results.json(os.path.join(directory, "results.json"))

    with caplog.at_level(logging.WARNING):

        target_result = EvaluatorAnalysisFactory.analyze(
            optimization=optimization,
            target=target,
            target_directory=directory,
            result_directory=directory,
            reindex=False,
        )

    assert (
        "The reference data set contains properties "
        "with ids that cannot be cast to integers" in caplog.text
    )

    assert numpy.isclose(target_result.objective_function, 1.0)
    assert len(target_result.statistic_entries) == 1


def test_analyze_target_missing(mock_target):

    optimization, target, _ = mock_target

    assert (
        EvaluatorAnalysisFactory.analyze(
            optimization=optimization,
            target=target,
            target_directory="",
            result_directory="",
            reindex=True,
        )
        is None
    )
