import os
import sys

from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.factory import (
    create_data_set,
    create_evaluator_target,
    create_optimization,
    create_optimization_result,
)


def test_plot(force_field, monkeypatch):

    from nonbonded.library.plotting.seaborn import optimization as optimization_module

    # Mock the required file inputs
    data_set = create_data_set("data-set-1", 1)
    data_set_collection = DataSetCollection(data_sets=[data_set])

    optimization = create_optimization(
        "project-1",
        "study-1",
        "optimization-1",
        [create_evaluator_target("target-1", ["data-set-1"])],
    )
    optimization_result = create_optimization_result(
        "project-1", "study-1", "optimization-1", ["target-1"], []
    )

    # Mock the already tested plotting methods.
    monkeypatch.setattr(
        optimization_module, "plot_parameter_changes", lambda *args: None
    )
    monkeypatch.setattr(
        optimization_module, "plot_objective_per_iteration", lambda *args: None
    )
    monkeypatch.setattr(optimization_module, "plot_rmse_change", lambda *args: None)

    if "nonbonded.library.factories.plots.optimization" in sys.modules:
        sys.modules.pop("nonbonded.library.factories.plots.optimization")

    from nonbonded.library.factories.plots.optimization import OptimizationPlotFactory

    with temporary_cd():

        # Save the inputs in their expected locations.
        data_set_collection.to_file("test-set-collection.json")
        optimization.to_file("optimization.json")
        os.makedirs("analysis")
        optimization_result.to_file(
            os.path.join("analysis", "optimization-results.json")
        )

        OptimizationPlotFactory.plot([""], "png")

        assert os.path.isdir("plots")
