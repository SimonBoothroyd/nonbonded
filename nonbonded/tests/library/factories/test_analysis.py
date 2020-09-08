import logging
import os

from nonbonded.library.factories.analysis.benchmark import BenchmarkFactory
from nonbonded.library.factories.analysis.optimization import OptimizationFactory
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.forcefield import ForceField
from nonbonded.library.utilities import temporary_cd
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_data_set,
    create_evaluator_target,
    create_optimization,
)


def _mock_analyse_functional_groups(*_):
    return {}


def test_benchmark_analysis(caplog, monkeypatch):

    from openff.evaluator.client import RequestResult
    from openff.evaluator.datasets import PhysicalPropertyDataSet

    # Patch checkmol call as it is not being tested here
    from nonbonded.library.utilities import checkmol

    monkeypatch.setattr(
        checkmol, "analyse_functional_groups", _mock_analyse_functional_groups
    )

    benchmark = create_benchmark(
        "project-1", "study-1", "benchmark-1", ["data-set-1"], "optimization-1", None
    )

    # Create a reference data set.
    reference_data_set = create_data_set("data-set-1")
    reference_data_set.entries.append(reference_data_set.entries[0].copy())
    reference_data_set.entries[0].id = 1
    reference_data_set.entries[1].id = 2

    # Create a set of evaluator results
    estimated_data_set = PhysicalPropertyDataSet()
    estimated_data_set.add_properties(reference_data_set.entries[0].to_evaluator())

    unsuccessful_properties = PhysicalPropertyDataSet()
    unsuccessful_properties.add_properties(reference_data_set.entries[1].to_evaluator())

    results = RequestResult()
    results.estimated_properties = estimated_data_set
    results.unsuccessful_properties = unsuccessful_properties

    with temporary_cd():

        # Save the expected input files.
        with open("benchmark.json", "w") as file:
            file.write(benchmark.json())

        with open("test-set-collection.json", "w") as file:
            file.write(DataSetCollection(data_sets=[reference_data_set]).json())

        results.json("results.json")

        with caplog.at_level(logging.WARNING):
            BenchmarkFactory.generate(benchmark, True)

        assert (
            "1 properties could not be estimated and so were not analyzed"
            in caplog.text
        )

        assert os.path.isdir("analysis")
        assert os.path.isfile(os.path.join("analysis", "benchmark-results.json"))


def test_optimization_analysis(monkeypatch):

    from forcebalance import nifty
    from openff.evaluator.client import RequestResult
    from openforcefield.typing.engines.smirnoff import ForceField as OFFForceField

    # Patch checkmol call as it is not being tested here
    from nonbonded.library.utilities import checkmol

    monkeypatch.setattr(
        checkmol, "analyse_functional_groups", _mock_analyse_functional_groups
    )

    target = create_evaluator_target("evaluator-target-1", ["data-set-1"])

    optimization = create_optimization(
        "project-1", "study-1", "optimization-1", [target]
    )
    optimization.force_field = ForceField.from_openff(
        OFFForceField(
            '<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL"></SMIRNOFF>'
        )
    )

    # Create a reference data set.
    reference_data_set = create_data_set("data-set-1")
    reference_data_set.entries[0].id = 1

    # Create a set of evaluator results
    results = RequestResult()
    results.estimated_properties = reference_data_set.to_evaluator()

    with temporary_cd():

        # Save the expected input / results files.
        os.makedirs(os.path.join("result", "optimize"))
        os.makedirs(os.path.join("targets", target.id))
        os.makedirs(os.path.join("optimize.tmp", target.id, "iter_0000"))

        with open("optimization.json", "w") as file:
            file.write(optimization.json())

        optimization.force_field.to_openff().to_file(
            os.path.join("result", "optimize", "force-field.offxml")
        )

        # Mock opening the objective function file.
        monkeypatch.setattr(nifty, "lp_load", lambda x: {"X": 1.0})

        with open(
            os.path.join("targets", target.id, "training-set-collection.json"), "w"
        ) as file:

            file.write(DataSetCollection(data_sets=[reference_data_set]).json())

        results.json(
            os.path.join("optimize.tmp", target.id, "iter_0000", "results.json")
        )

        OptimizationFactory.generate(optimization, True)

        assert os.path.isdir(os.path.join("analysis", "evaluator-target-1"))
        assert os.path.isfile(
            os.path.join("analysis", "evaluator-target-1", "iteration-0.json")
        )

        assert os.path.isfile(os.path.join("analysis", "optimization-results.json"))
