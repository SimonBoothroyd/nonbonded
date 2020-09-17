import os
from typing import List, Tuple

import numpy
import pytest
from typing_extensions import Literal

from nonbonded.library.models.forcefield import ForceField, Parameter
from nonbonded.library.models.projects import Optimization
from nonbonded.library.models.results import OptimizationResult
from nonbonded.library.plotting.optimization import (
    _extract_parameter_value,
    _parameter_attribute_to_title,
    plot_objective_per_iteration,
    plot_parameter_changes,
    plot_rmse_change,
)
from nonbonded.tests.utilities.factory import (
    create_evaluator_target,
    create_optimization,
    create_optimization_result,
    create_recharge_target,
)


@pytest.fixture()
def optimizations_and_results(
    smirnoff_force_field,
) -> Tuple[List[Optimization], List[OptimizationResult]]:

    optimization_1 = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["molecule-set-1"]),
        ],
    )
    optimization_1.name = "Optimization 1"
    optimization_1.force_field = ForceField.from_openff(smirnoff_force_field)
    optimization_2 = create_optimization(
        "project-1",
        "study-1",
        "optimization-2",
        [
            create_evaluator_target("evaluator-target-1", ["data-set-1"]),
            create_recharge_target("recharge-target-1", ["molecule-set-1"]),
        ],
    )
    optimization_2.force_field = ForceField.from_openff(smirnoff_force_field)
    optimization_2.name = "Optimization 2"

    smirnoff_force_field.get_parameter_handler("vdW").parameters["[#6:1]"].epsilon *= 2
    smirnoff_force_field.get_parameter_handler("vdW").parameters["[#6:1]"].sigma *= 3

    optimization_result_1 = create_optimization_result(
        "project-1",
        "study-1",
        "optimization-1",
        ["evaluator-target-1"],
        ["recharge-target-1"],
    )
    optimization_result_1.refit_force_field = ForceField.from_openff(
        smirnoff_force_field
    )

    smirnoff_force_field.get_parameter_handler("vdW").parameters["[#6:1]"].epsilon /= 4
    smirnoff_force_field.get_parameter_handler("vdW").parameters["[#6:1]"].sigma /= 6

    optimization_result_2 = create_optimization_result(
        "project-1",
        "study-1",
        "optimization-2",
        ["evaluator-target-1"],
        ["recharge-target-1"],
    )
    optimization_result_2.refit_force_field = ForceField.from_openff(
        smirnoff_force_field
    )

    return (
        [optimization_1, optimization_2],
        [optimization_result_1, optimization_result_2],
    )


def test_extract_parameter_value(smirnoff_force_field):

    value = _extract_parameter_value(
        smirnoff_force_field,
        Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="epsilon"),
    )
    assert numpy.isclose(value, 1.0 / 4.184)


@pytest.mark.parametrize(
    "parameter, expected",
    [
        (
            Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="missing"),
            "missing",
        ),
        (
            Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="sigma"),
            r"$\sigma$",
        ),
        (
            Parameter(
                handler_type="vdW", smirks="[#6:1]", attribute_name="charge_increment2"
            ),
            r"$q_{2}$",
        ),
    ],
)
def test_parameter_attribute_to_title(parameter, expected):
    assert _parameter_attribute_to_title(parameter) == expected


@pytest.mark.parametrize("mode", ["percent", "absolute"])
@pytest.mark.parametrize("file_type", ["png", "pdf"])
def test_plot_parameter_changes(
    optimizations_and_results,
    mode: Literal["percent", "absolute"],
    file_type: Literal["png", "pdf"],
    tmpdir,
):

    optimizations, results = optimizations_and_results

    plot_parameter_changes(
        optimizations,
        results,
        mode,
        True,
        tmpdir,
        file_type,
    )

    assert os.path.isfile(os.path.join(tmpdir, f"vdw-{mode}-change.{file_type}"))


@pytest.mark.parametrize("file_type", ["png", "pdf"])
def test_plot_objective_per_iteration(
    optimizations_and_results, file_type: Literal["png", "pdf"], tmpdir
):

    optimizations, results = optimizations_and_results

    plot_objective_per_iteration(optimizations, results, True, tmpdir, file_type)

    assert os.path.isfile(os.path.join(tmpdir, f"objective-function.{file_type}"))


@pytest.mark.parametrize("file_type", ["png", "pdf"])
def test_plot_rmse_change(
    optimizations_and_results, file_type: Literal["png", "pdf"], tmpdir
):

    _, results = optimizations_and_results

    optimization_result = results[0].copy(deep=True)
    optimization_result.target_results[1] = {}

    for target_id in optimization_result.target_results[0]:

        target_result = optimization_result.target_results[0][target_id].copy(deep=True)

        for statistic in target_result.statistic_entries:

            statistic.value *= 0.5
            statistic.lower_95_ci *= 0.5
            statistic.upper_95_ci *= 0.5

        optimization_result.target_results[1][target_id] = target_result

    plot_rmse_change(optimization_result, tmpdir, file_type)

    assert os.path.isfile(
        os.path.join(tmpdir, f"evaluator-target-1-density-2-rmse.{file_type}")
    )
    assert os.path.isfile(os.path.join(tmpdir, f"recharge-target-1-rmse.{file_type}"))


def test_plot_rmse_change_missing_iteration(optimizations_and_results, tmpdir):

    _, results = optimizations_and_results

    optimization_result = results[0].copy(deep=True)

    with pytest.raises(KeyError) as error_info:
        plot_rmse_change(optimization_result, tmpdir, "png")

    assert "at least two iterations to plot the change in RMSE values" in str(
        error_info.value
    )

    optimization_result.target_results.pop(0)

    with pytest.raises(KeyError) as error_info:
        plot_rmse_change(optimization_result, tmpdir, "png")

    assert "must contain the statistics for iteration 0" in str(error_info.value)
