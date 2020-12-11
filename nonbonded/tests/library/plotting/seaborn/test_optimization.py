import os

import numpy
import pytest
from typing_extensions import Literal

from nonbonded.library.models.forcefield import Parameter
from nonbonded.library.plotting.seaborn.optimization import (
    _extract_parameter_value,
    _parameter_attribute_to_title,
    plot_objective_per_iteration,
    plot_parameter_changes,
    plot_rmse_change,
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

    optimizations, results = optimizations_and_results

    optimization_result = results[0].copy(deep=True)
    optimization_result.target_results[1] = {}

    for target_id in optimization_result.target_results[0]:

        target_result = optimization_result.target_results[0][target_id].copy(deep=True)

        for statistic in target_result.statistic_entries:

            statistic.value *= 0.5
            statistic.lower_95_ci *= 0.5
            statistic.upper_95_ci *= 0.5

        optimization_result.target_results[1][target_id] = target_result

    plot_rmse_change(optimizations[0], optimization_result, tmpdir, file_type)

    assert os.path.isfile(
        os.path.join(tmpdir, f"evaluator-target-1-density-2-rmse.{file_type}")
    )
    assert os.path.isfile(
        os.path.join(tmpdir, f"recharge-target-1-esp-rmse.{file_type}")
    )


def test_plot_rmse_change_missing_iteration(optimizations_and_results, tmpdir):

    optimizations, results = optimizations_and_results

    optimization_result = results[0].copy(deep=True)
    del optimization_result.target_results[1]

    with pytest.raises(KeyError) as error_info:
        plot_rmse_change(optimizations[0], optimization_result, tmpdir, "png")

    assert "at least two iterations to plot the change in RMSE values" in str(
        error_info.value
    )

    optimization_result.target_results.pop(0)

    with pytest.raises(KeyError) as error_info:
        plot_rmse_change(optimizations[0], optimization_result, tmpdir, "png")

    assert "must contain the statistics for iteration 0" in str(error_info.value)
