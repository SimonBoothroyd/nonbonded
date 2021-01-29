import os

import pytest
from forcebalance.nifty import lp_dump

from nonbonded.library.factories.analysis.optimization import (
    OptimizationAnalysisFactory,
)
from nonbonded.library.factories.analysis.targets.evaluator import (
    EvaluatorAnalysisFactory,
)
from nonbonded.library.factories.analysis.targets.recharge import (
    RechargeAnalysisFactory,
)
from nonbonded.library.models.results import (
    EvaluatorTargetResult,
    OptimizationResult,
    RechargeTargetResult,
)
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.factory import (
    create_evaluator_target,
    create_optimization,
    create_recharge_target,
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


def test_analysis(monkeypatch, force_field, dummy_conda_env):

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["qc-data-set-1"]),
        ],
    )
    optimization.force_field = force_field

    with temporary_cd(os.path.dirname(dummy_conda_env)):

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
            EvaluatorAnalysisFactory,
            "analyze",
            lambda *args: EvaluatorTargetResult(
                objective_function=1.0, statistic_entries=[]
            ),
        )
        monkeypatch.setattr(
            RechargeAnalysisFactory,
            "analyze",
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


def test_analysis_n_iteration(monkeypatch, force_field):
    """Test that the correction exception is raised in the case where a refit
    force field is found but no target outputs are."""

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["qc-data-set-1"]),
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


def test_analysis_missing_result(monkeypatch, force_field):
    """Test that the correction exception is raised in the case where a the
    expected results of a target are missing."""

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["qc-data-set-1"]),
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
            EvaluatorAnalysisFactory,
            "analyze",
            lambda *args: EvaluatorTargetResult(
                objective_function=1.0, statistic_entries=[]
            ),
        )
        monkeypatch.setattr(
            RechargeAnalysisFactory,
            "analyze",
            lambda *args: None,
        )

        with pytest.raises(RuntimeError) as error_info:
            OptimizationAnalysisFactory.analyze(True)

        assert "The results of the recharge-target-1 target could not be found" in str(
            error_info.value
        )
