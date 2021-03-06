import numpy
import pytest
from openff.evaluator import unit
from openff.evaluator.datasets import PhysicalPropertyDataSet, PropertyPhase
from openff.evaluator.properties import Density, EnthalpyOfMixing
from openff.evaluator.substances import Substance
from openff.evaluator.thermodynamics import ThermodynamicState
from pydantic import ValidationError

from nonbonded.library.models.authors import Author
from nonbonded.library.models.datasets import Component, DataSet, DataSetEntry
from nonbonded.library.models.results import (
    BenchmarkResult,
    DataSetResult,
    OptimizationResult,
    RechargeTargetResult,
)
from nonbonded.library.statistics.statistics import StatisticType
from nonbonded.library.utilities.environments import ChemicalEnvironment
from nonbonded.tests.utilities.comparison import does_not_raise
from nonbonded.tests.utilities.factory import create_force_field, create_statistic


@pytest.fixture(scope="module")
def estimated_reference_sets():
    estimated_density = Density(
        thermodynamic_state=ThermodynamicState(
            298.15 * unit.kelvin, pressure=1.0 * unit.atmosphere
        ),
        phase=PropertyPhase.Liquid,
        substance=Substance.from_components("O", "CC=O"),
        value=1.0 * unit.kilogram / unit.meter ** 3,
        uncertainty=0.1 * unit.kilogram / unit.meter ** 3,
    )
    estimated_density.id = "1"
    estimated_enthalpy = EnthalpyOfMixing(
        thermodynamic_state=ThermodynamicState(
            298.15 * unit.kelvin, pressure=1.0 * unit.atmosphere
        ),
        phase=PropertyPhase.Liquid,
        substance=Substance.from_components("O", "CC=O"),
        value=1.0 * unit.kilocalorie / unit.mole,
        uncertainty=0.1 * unit.kilojoule / unit.mole,
    )
    estimated_enthalpy.id = "2"

    estimated_data_set = PhysicalPropertyDataSet()
    estimated_data_set.add_properties(estimated_density, estimated_enthalpy)

    reference_density = DataSetEntry(
        id=1,
        property_type="Density",
        temperature=298.15,
        pressure=101.325,
        value=0.001,
        std_error=0.0001,
        doi=" ",
        components=[
            Component(smiles="O", mole_fraction=0.5),
            Component(smiles="CC=O", mole_fraction=0.5),
        ],
    )
    reference_enthalpy = DataSetEntry(
        id=2,
        property_type="EnthalpyOfMixing",
        temperature=298.15,
        pressure=101.325,
        value=4.184,
        std_error=0.1,
        doi=" ",
        components=[
            Component(smiles="O", mole_fraction=0.5),
            Component(smiles="CC=O", mole_fraction=0.5),
        ],
    )

    reference_data_set = DataSet(
        id="ref",
        description=" ",
        authors=[Author(name=" ", email="x@x.com", institute=" ")],
        entries=[reference_density, reference_enthalpy],
    )

    return estimated_data_set, reference_data_set


def test_evaluator_to_results_entries(estimated_reference_sets):
    """Tests the private `_evaluator_to_results_entries` function of `AnalysedResult`"""

    estimated_data_set, reference_data_set = estimated_reference_sets
    reference_entries = {x.id: x for x in reference_data_set.entries}

    assert len(estimated_data_set) == len(reference_data_set.entries)

    analysis_environments = [ChemicalEnvironment.Aqueous, ChemicalEnvironment.Aldehyde]

    results_entries, results_frame = DataSetResult._evaluator_to_results_entries(
        reference_data_set, estimated_data_set, analysis_environments
    )

    assert len(results_entries) == len(estimated_data_set)
    assert len(results_frame) == len(estimated_data_set)

    for results_entry in results_entries:

        reference_entry = reference_entries[results_entry.reference_id]

        assert numpy.isclose(results_entry.estimated_value, reference_entry.value)
        assert numpy.isclose(
            results_entry.estimated_std_error, reference_entry.std_error
        )

        assert results_entry.categories == ["Aldehyde ~ Aqueous"]


def test_analysed_result_from_evaluator():
    """Tests the `AnalysedResult.from_evaluator` function."""
    expected_mean = 0.0
    expected_std = numpy.random.rand() + 1.0

    values = numpy.random.normal(expected_mean, expected_std, 1000)

    estimated_properties = []
    reference_entries = []

    for index, value in enumerate(values):
        property_id = index + 1

        estimated_density = Density(
            thermodynamic_state=ThermodynamicState(
                298.15 * unit.kelvin, pressure=1.0 * unit.atmosphere
            ),
            phase=PropertyPhase.Liquid,
            substance=Substance.from_components("O"),
            value=value * Density.default_unit(),
            uncertainty=0.0 * Density.default_unit(),
        )
        estimated_density.id = str(property_id)
        estimated_properties.append(estimated_density)

        reference_density = DataSetEntry(
            id=property_id,
            property_type="Density",
            temperature=298.15,
            pressure=101.325,
            value=expected_mean,
            std_error=None,
            doi=" ",
            components=[Component(smiles="O", mole_fraction=1.0)],
        )
        reference_entries.append(reference_density)

    estimated_data_set = PhysicalPropertyDataSet()
    estimated_data_set.add_properties(*estimated_properties)

    reference_data_set = DataSet(
        id="ref",
        description=" ",
        authors=[Author(name=" ", email="x@x.com", institute=" ")],
        entries=reference_entries,
    )

    analysis_environments = [ChemicalEnvironment.Aqueous]

    analysed_results = DataSetResult.from_evaluator(
        reference_data_set=reference_data_set,
        estimated_data_set=estimated_data_set,
        analysis_environments=analysis_environments,
        statistic_types=[StatisticType.RMSE],
        bootstrap_iterations=1000,
    )

    assert len(analysed_results.result_entries) == len(estimated_properties)

    full_statistics = next(
        iter(x for x in analysed_results.statistic_entries if x.category is None)
    )

    assert full_statistics.property_type == "Density"
    assert full_statistics.n_components == 1
    assert full_statistics.statistic_type == StatisticType.RMSE
    assert numpy.isclose(full_statistics.value, expected_std, rtol=0.10)


def test_benchmark_result_from_evaluator(estimated_reference_sets):
    """Tests the `BenchmarkResult.from_evaluator` function."""
    estimated_data_set, reference_data_set = estimated_reference_sets

    benchmark_result = BenchmarkResult.from_evaluator(
        project_id="a",
        study_id="b",
        benchmark_id="c",
        reference_data_set=reference_data_set,
        estimated_data_set=estimated_data_set,
        analysis_environments=[
            ChemicalEnvironment.Aqueous,
            ChemicalEnvironment.Aldehyde,
        ],
    )

    assert benchmark_result.data_set_result is not None
    assert len(benchmark_result.data_set_result.result_entries) == len(
        estimated_data_set
    )
    # 3 statistic types x 2 properties x 2 categories
    assert len(benchmark_result.data_set_result.statistic_entries) == 12


@pytest.mark.parametrize(
    "result_kwargs, expected_raises",
    [
        (
            dict(
                project_id="project-1",
                study_id="study-1",
                id="optimization-1",
                target_results={
                    0: {
                        "target-1": RechargeTargetResult(
                            objective_function=0.0,
                            statistic_entries=[create_statistic()],
                        )
                    }
                },
                refit_force_field=create_force_field(),
            ),
            does_not_raise(),
        ),
        (
            dict(
                project_id="project-1",
                study_id="study-1",
                id="optimization-1",
                target_results={},
                refit_force_field=create_force_field(),
            ),
            pytest.raises(ValidationError),
        ),
        (
            dict(
                project_id="project-1",
                study_id="study-1",
                id="optimization-1",
                target_results={0: {}},
                refit_force_field=create_force_field(),
            ),
            pytest.raises(ValidationError),
        ),
        (
            dict(
                project_id="project-1",
                study_id="study-1",
                id="optimization-1",
                target_results={
                    0: {
                        "target-1": RechargeTargetResult(
                            objective_function=0.0,
                            statistic_entries=[create_statistic()],
                        )
                    },
                    1: {
                        "target-2": RechargeTargetResult(
                            objective_function=0.0,
                            statistic_entries=[create_statistic()],
                        )
                    },
                },
                refit_force_field=create_force_field(),
            ),
            pytest.raises(ValidationError),
        ),
        (
            dict(
                project_id="project-1",
                study_id="study-1",
                id="optimization-1",
                target_results={
                    0: {
                        "target-1": RechargeTargetResult(
                            objective_function=0.0,
                            statistic_entries=[create_statistic()],
                        )
                    },
                    1: {},
                },
                refit_force_field=create_force_field(),
            ),
            pytest.raises(ValidationError),
        ),
    ],
)
def test_validate_optimization_result(result_kwargs, expected_raises):

    with expected_raises:
        OptimizationResult(**result_kwargs)
