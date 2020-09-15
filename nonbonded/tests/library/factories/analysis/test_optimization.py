import json
import os

import numpy
import pytest
from forcebalance.nifty import lp_dump
from openff.evaluator.client import RequestResult

from nonbonded.library.factories.analysis.optimization import (
    OptimizationAnalysisFactory,
)
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.results import (
    EvaluatorTargetResult,
    OptimizationResult,
    RechargeTargetResult,
)
from nonbonded.library.utilities import temporary_cd
from nonbonded.library.utilities.environments import ChemicalEnvironment
from nonbonded.tests.utilities.factory import (
    create_data_set,
    create_evaluator_target,
    create_optimization,
    create_recharge_target,
)


def test_read_objective_function(tmpdir):

    # Save an objective function file.
    lp_dump({"X": 1.0}, os.path.join(tmpdir, "objective.p"))

    assert numpy.isclose(
        OptimizationAnalysisFactory._read_objective_function(tmpdir), 1.0
    )


def test_load_refit_force_field(tmpdir, smirnoff_force_field):

    with temporary_cd(str(tmpdir)):

        os.makedirs(os.path.join("result", "optimize"))

        smirnoff_force_field.to_file(
            os.path.join(
                tmpdir, os.path.join("result", "optimize", "force-field.offxml")
            )
        )

        refit_force_field = OptimizationAnalysisFactory._load_refit_force_field()
        assert refit_force_field.inner_content == smirnoff_force_field.to_string()


def test_load_refit_force_field_missing(smirnoff_force_field):

    with pytest.raises(FileNotFoundError):
        OptimizationAnalysisFactory._load_refit_force_field()


def test_analyze_evaluator_target(tmpdir):

    with temporary_cd(str(tmpdir)):

        # Mock the target to analyze.
        target = create_evaluator_target("evaluator-target-1", ["data-set-1"])
        os.makedirs(os.path.join("targets", target.id))

        optimization = create_optimization(
            "project-1", "study-1", "optimization-1", [target]
        )
        optimization.analysis_environments = []

        # Create a dummy data set and estimated result.
        reference_data_set = create_data_set("data-set-1", 1)
        DataSetCollection(data_sets=[reference_data_set]).to_file(
            os.path.join("targets", target.id, "training-set-collection.json")
        )

        results = RequestResult()
        results.estimated_properties = reference_data_set.to_evaluator()
        results.json("results.json")

        lp_dump({"X": 1.0}, "objective.p")

        # Analyze the mocked results
        target_result = OptimizationAnalysisFactory._analyze_evaluator_target(
            optimization=optimization, target=target, target_directory="", reindex=True
        )

    assert numpy.isclose(target_result.objective_function, 1.0)
    assert len(target_result.statistic_entries) == 1


def test_analyze_evaluator_target_missing(tmpdir):

    target = create_evaluator_target("evaluator-target-1", ["data-set-1"])

    optimization = create_optimization(
        "project-1", "study-1", "optimization-1", [target]
    )

    assert (
        OptimizationAnalysisFactory._analyze_evaluator_target(
            optimization=optimization, target=target, target_directory="", reindex=True
        )
        is None
    )


def test_analyze_recharge_target(tmpdir):

    with temporary_cd(str(tmpdir)):

        # Mock the target to analyze.
        target = create_recharge_target("recharge-target-1", ["molecule-set-1"])
        os.makedirs(os.path.join("targets", target.id))

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

        # Analyze the mocked results
        target_result = OptimizationAnalysisFactory._analyze_recharge_target(
            optimization=optimization,
            target=target,
            target_directory="",
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


def test_analyze_recharge_target_missing(tmpdir):

    target = create_recharge_target("recharge-target-1", ["molecule-set-1"])

    optimization = create_optimization(
        "project-1", "study-1", "optimization-1", [target]
    )

    assert (
        OptimizationAnalysisFactory._analyze_recharge_target(
            optimization=optimization, target=target, target_directory=""
        )
        is None
    )


def test_optimization_analysis(monkeypatch, force_field):

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["molecule-set-1"]),
        ],
    )
    optimization.force_field = force_field

    with temporary_cd():

        # Save the expected results files.
        os.makedirs(os.path.join("result", "optimize"))

        for target in optimization.targets:
            os.makedirs(os.path.join("targets", target.id))

            os.makedirs(os.path.join("optimize.tmp", target.id, "iter_0000"))
            os.makedirs(os.path.join("optimize.tmp", target.id, "iter_0001"))

            # Add enough output files to make it look like only one full iteration has
            # finished.
            lp_dump(
                {"X": 1.0},
                os.path.join("optimize.tmp", target.id, "iter_0000", "objective.p"),
            )

        lp_dump(
            {"X": 1.0},
            os.path.join(
                "optimize.tmp", optimization.targets[0].id, "iter_0001", "objective.p"
            ),
        )

        with open("optimization.json", "w") as file:
            file.write(optimization.json())

        optimization.force_field.to_openff().to_file(
            os.path.join("result", "optimize", "force-field.offxml")
        )

        # Mock the already tested functions.
        monkeypatch.setattr(
            OptimizationAnalysisFactory, "_load_refit_force_field", lambda: force_field
        )
        monkeypatch.setattr(
            OptimizationAnalysisFactory,
            "_analyze_evaluator_target",
            lambda *args: EvaluatorTargetResult(
                objective_function=1.0, statistic_entries=[]
            ),
        )
        monkeypatch.setattr(
            OptimizationAnalysisFactory,
            "_analyze_recharge_target",
            lambda *args: RechargeTargetResult(
                objective_function=1.0, statistic_entries=[]
            ),
        )

        OptimizationAnalysisFactory.analyze(True)

        for target in optimization.targets:

            assert os.path.isfile(
                os.path.join("analysis", target.id, "iteration-0.json")
            )
            assert not os.path.isfile(
                os.path.join("analysis", target.id, "iteration-1.json")
            )

        result = OptimizationResult.parse_file(
            os.path.join("analysis", "optimization-results.json")
        )

        assert len(result.target_results) == 1
        assert all(
            target.id in result.target_results[0] for target in optimization.targets
        )
        assert result.refit_force_field.inner_content == force_field.inner_content


def test_optimization_analysis_n_iteration(monkeypatch, force_field):
    """Test that the correction exception is raised in the case where a refit
    force field is found but no target outputs are."""

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["molecule-set-1"]),
        ],
    )
    optimization.force_field = force_field

    with temporary_cd():

        # Save the mock optimization file.
        with open("optimization.json", "w") as file:
            file.write(optimization.json())

        # Mock successfully reading a refit force field.
        monkeypatch.setattr(
            OptimizationAnalysisFactory, "_load_refit_force_field", lambda: force_field
        )

        with pytest.raises(RuntimeError) as error_info:
            OptimizationAnalysisFactory.analyze(True)

        assert "No iteration results could be found" in str(error_info.value)


def test_optimization_analysis_missing_result(monkeypatch, force_field):
    """Test that the correction exception is raised in the case where a the
    expected results of a target are missing."""

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["molecule-set-1"]),
        ],
    )
    optimization.force_field = force_field

    with temporary_cd():

        # Save the expected results files.
        os.makedirs(os.path.join("result", "optimize"))

        for target in optimization.targets:
            os.makedirs(os.path.join("targets", target.id))
            os.makedirs(os.path.join("optimize.tmp", target.id, "iter_0000"))

            lp_dump(
                {"X": 1.0},
                os.path.join("optimize.tmp", target.id, "iter_0000", "objective.p"),
            )

        with open("optimization.json", "w") as file:
            file.write(optimization.json())

        monkeypatch.setattr(
            OptimizationAnalysisFactory, "_load_refit_force_field", lambda: force_field
        )

        # Mock a missing target result.
        monkeypatch.setattr(
            OptimizationAnalysisFactory,
            "_analyze_evaluator_target",
            lambda *args: EvaluatorTargetResult(
                objective_function=1.0, statistic_entries=[]
            ),
        )
        monkeypatch.setattr(
            OptimizationAnalysisFactory,
            "_analyze_recharge_target",
            lambda *args: None,
        )

        with pytest.raises(RuntimeError) as error_info:
            OptimizationAnalysisFactory.analyze(True)

        assert "The results of the recharge-target-1 target could not be found" in str(
            error_info.value
        )
