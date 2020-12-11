from nonbonded.library.models.results import RechargeTargetResult, Statistic
from nonbonded.library.plotting.plotly.optimization import (
    plot_objective_per_iteration,
    plot_target_rmse,
)
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.tests.utilities.factory import create_recharge_target


def test_plot_objective_per_iteration(optimizations_and_results, tmpdir):

    optimizations, results = optimizations_and_results

    figure = plot_objective_per_iteration(optimizations, results)

    assert figure is not None
    assert figure.to_plotly() is not None


def test_plot_target_rmse(tmpdir):

    initial_result = RechargeTargetResult(
        objective_function=0.5,
        statistic_entries=[
            Statistic(
                statistic_type=StatisticType.RMSE,
                value=1.0,
                lower_95_ci=0.95,
                upper_95_ci=1.05,
                category="Alcohol",
            )
        ],
    )
    final_result = RechargeTargetResult(
        objective_function=0.5,
        statistic_entries=[
            Statistic(
                statistic_type=StatisticType.RMSE,
                value=0.5,
                lower_95_ci=0.4,
                upper_95_ci=0.6,
                category="Alcohol",
            )
        ],
    )

    figures = plot_target_rmse(
        [create_recharge_target("target-1", ["data-set-1"])] * 2,
        [initial_result, final_result],
        ["Initial", "Final"],
    )

    assert "esp" in figures
    figure = figures["esp"]

    assert len(figure.subplots) == 1
    assert len(figure.subplots[0].traces) == 2

    assert figure is not None
    assert figure.to_plotly() is not None
