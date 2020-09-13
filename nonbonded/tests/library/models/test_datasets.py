import numpy
import pytest
from openff.evaluator import unit
from openff.evaluator.datasets import (
    MeasurementSource,
    PhysicalProperty,
    PhysicalPropertyDataSet,
    PropertyPhase,
)
from openff.evaluator.properties import (
    Density,
    EnthalpyOfMixing,
    EnthalpyOfVaporization,
    ExcessMolarVolume,
    SolvationFreeEnergy,
)
from openff.evaluator.substances import Component, ExactAmount, MoleFraction, Substance
from openff.evaluator.thermodynamics import ThermodynamicState
from pydantic import ValidationError

from nonbonded.library.models.authors import Author
from nonbonded.library.models.datasets import (
    DataSet,
    DataSetCollection,
    DataSetEntry,
    MoleculeSet,
    MoleculeSetCollection,
)
from nonbonded.library.utilities.exceptions import UnrecognisedPropertyType
from nonbonded.tests.utilities.factory import create_data_set, create_molecule_set


def compare_properties(
    evaluator_property: PhysicalProperty, data_set_entry: DataSetEntry
):
    """Compares whether an evaluator property is equivalent to a
    data set entry

    Parameters
    ----------
    evaluator_property
        The evaluator property to compare.
    data_set_entry
        The data set entry to compare.

    Raises
    ------
    AssertionError
    """

    assert data_set_entry.property_type == evaluator_property.__class__.__name__
    assert len(data_set_entry.components) == len(evaluator_property.substance)

    expected_components = {x.smiles: x for x in evaluator_property.substance}

    for component in data_set_entry.components:

        assert component.smiles in expected_components

        evaluator_component = expected_components.pop(component.smiles)

        amount = evaluator_property.substance.get_amounts(evaluator_component)[0]

        if isinstance(amount, MoleFraction):
            assert numpy.isclose(component.mole_fraction, amount.value)
            assert component.exact_amount == 0
        elif isinstance(amount, ExactAmount):
            assert component.exact_amount == amount.value
            assert numpy.isclose(component.mole_fraction, 0.0)
        else:
            raise NotImplementedError()

        assert component.role == "Solvent"

    assert numpy.isclose(
        data_set_entry.value,
        evaluator_property.value.to(evaluator_property.default_unit()).magnitude,
    )
    assert numpy.isclose(
        data_set_entry.std_error,
        evaluator_property.uncertainty.to(evaluator_property.default_unit()).magnitude,
    )

    assert numpy.isclose(
        data_set_entry.temperature,
        evaluator_property.thermodynamic_state.temperature.to(unit.kelvin).magnitude,
    )
    assert numpy.isclose(
        data_set_entry.pressure,
        evaluator_property.thermodynamic_state.pressure.to(unit.kilopascal).magnitude,
    )

    assert data_set_entry.phase == str(evaluator_property.phase)
    # noinspection PyUnresolvedReferences
    assert data_set_entry.doi == evaluator_property.source.doi


def compare_evaluator_properties(property_1, property_2):
    """Compares whether two evaluator properties are equivalent.

    Parameters
    ----------
    property_1
        The first property to compare.
    property_2
        The second property to compare.

    Raises
    ------
    AssertionError
    """
    assert property_2.substance.identifier == property_1.substance.identifier
    assert property_2.phase == property_1.phase

    assert property_2.thermodynamic_state == property_1.thermodynamic_state

    assert numpy.isclose(property_2.value, property_1.value)
    assert numpy.isclose(property_2.uncertainty, property_1.uncertainty)

    # noinspection PyUnresolvedReferences
    assert property_2.source.doi == property_1.source.doi


def simple_evaluator_data_set():
    """Create a simple evaluator `PhysicalPropertyDataSet` which contains
    a simple binary density measurement.

    Returns
    -------
    PhysicalPropertyDataSet
    """

    evaluator_density = Density(
        thermodynamic_state=ThermodynamicState(
            298.15 * unit.kelvin, pressure=1.0 * unit.atmosphere
        ),
        phase=PropertyPhase.Liquid,
        substance=Substance.from_components("O", "CC=O"),
        value=1.0 * unit.kilogram / unit.meter ** 3,
        uncertainty=0.1 * unit.kilogram / unit.meter ** 3,
        source=MeasurementSource(doi="10.1000/xyz123"),
    )
    evaluator_density.id = "1"

    evaluator_data_set = PhysicalPropertyDataSet()
    evaluator_data_set.add_properties(evaluator_density)

    return evaluator_data_set


def complete_evaluator_data_set():
    """Create a more comprehensive `PhysicalPropertyDataSet` which contains one
    measurement for each of:

        * pure density
        * binary density
        * pure enthalpy of vaporization
        * binary enthalpy of mixing
        * binary excess molar volume
        * hydration free energy

    Returns
    -------
    PhysicalPropertyDataSet
    """
    thermodynamic_state = ThermodynamicState(
        298.15 * unit.kelvin, pressure=1.0 * unit.atmosphere
    )
    source = MeasurementSource(doi="10.1000/xyz123")

    solvation_substance = Substance()
    solvation_substance.add_component(Component("O"), MoleFraction(1.0))
    solvation_substance.add_component(Component("CCCO"), ExactAmount(1))

    evaluator_properties = [
        Density(
            thermodynamic_state=thermodynamic_state,
            phase=PropertyPhase.Liquid,
            substance=Substance.from_components("O"),
            value=1.0 * unit.kilogram / unit.meter ** 3,
            uncertainty=0.1 * unit.kilogram / unit.meter ** 3,
            source=source,
        ),
        Density(
            thermodynamic_state=thermodynamic_state,
            phase=PropertyPhase.Liquid,
            substance=Substance.from_components("O", "CC=O"),
            value=1.0 * unit.kilogram / unit.meter ** 3,
            uncertainty=0.1 * unit.kilogram / unit.meter ** 3,
            source=source,
        ),
        EnthalpyOfVaporization(
            thermodynamic_state=thermodynamic_state,
            phase=PropertyPhase(PropertyPhase.Liquid | PropertyPhase.Gas),
            substance=Substance.from_components("CCO"),
            value=1.0 * EnthalpyOfVaporization.default_unit(),
            uncertainty=0.1 * EnthalpyOfVaporization.default_unit(),
            source=source,
        ),
        EnthalpyOfMixing(
            thermodynamic_state=thermodynamic_state,
            phase=PropertyPhase.Liquid,
            substance=Substance.from_components("CCCCO", "CC(C=O)C"),
            value=1.0 * EnthalpyOfMixing.default_unit(),
            uncertainty=0.1 * EnthalpyOfMixing.default_unit(),
            source=source,
        ),
        ExcessMolarVolume(
            thermodynamic_state=thermodynamic_state,
            phase=PropertyPhase.Liquid,
            substance=Substance.from_components("C(=O)CCCO", "CCCCCC"),
            value=1.0 * ExcessMolarVolume.default_unit(),
            uncertainty=0.1 * ExcessMolarVolume.default_unit(),
            source=source,
        ),
        SolvationFreeEnergy(
            thermodynamic_state=thermodynamic_state,
            phase=PropertyPhase.Liquid,
            substance=solvation_substance,
            value=1.0 * SolvationFreeEnergy.default_unit(),
            uncertainty=0.1 * SolvationFreeEnergy.default_unit(),
            source=source,
        ),
    ]

    for index, evaluator_property in enumerate(evaluator_properties):
        evaluator_property.id = str(index + 1)

    evaluator_data_set = PhysicalPropertyDataSet()
    evaluator_data_set.add_properties(*evaluator_properties)

    return evaluator_data_set


@pytest.mark.parametrize(
    "evaluator_data_set", [simple_evaluator_data_set(), complete_evaluator_data_set()]
)
def test_from_pandas(evaluator_data_set):
    """A test that the `DataSet.from_pandas` function works as expected."""

    data_frame = evaluator_data_set.to_pandas()

    data_set = DataSet.from_pandas(
        data_frame,
        "id",
        description="Lorem Ipsum",
        authors=[Author(name=" ", email="x@x.com", institute=" ")],
    )

    assert data_set.id == "id"
    assert data_set.description == "Lorem Ipsum"
    assert len(data_set.authors) == 1

    assert len(data_set.entries) == len(evaluator_data_set)

    evaluator_properties_by_id = {x.id: x for x in evaluator_data_set}

    for entry in data_set.entries:

        evaluator_property = evaluator_properties_by_id[str(entry.id)]
        compare_properties(evaluator_property, entry)


@pytest.mark.parametrize(
    "evaluator_data_set", [simple_evaluator_data_set(), complete_evaluator_data_set()]
)
def test_evaluator_round_trip(evaluator_data_set):
    """A simple test that the `DataSet.from_pandas` and `DataSet.to_evaluator`
    functions work in conjunction with one another."""

    data_frame = evaluator_data_set.to_pandas()

    data_set = DataSet.from_pandas(
        data_frame,
        "id",
        description="Lorem Ipsum",
        authors=[Author(name=" ", email="x@x.com", institute=" ")],
    )

    recreated_data_set = data_set.to_evaluator()
    assert len(recreated_data_set) == len(evaluator_data_set)

    evaluator_properties_by_id = {x.id: x for x in evaluator_data_set}

    for recreated_property in recreated_data_set:

        evaluator_property = evaluator_properties_by_id[recreated_property.id]
        compare_evaluator_properties(evaluator_property, recreated_property)


def test_unrecognised_property():

    data_entry = create_data_set("data-set-1").entries[0]
    data_entry.property_type = "BasePropertyType"

    with pytest.raises(UnrecognisedPropertyType):
        data_entry.to_evaluator()


def test_pandas_string_id():

    data_series = create_data_set("data-set-1").entries[0].to_series()
    data_series["Id"] = "String"

    data_entry = DataSetEntry.from_series(data_series)
    assert data_entry.id is None


@pytest.mark.parametrize(
    "evaluator_data_set", [simple_evaluator_data_set(), complete_evaluator_data_set()]
)
def test_pandas_round_trip(evaluator_data_set):
    """A simple test that the `DataSet.from_pandas` and `DataSet.to_pandas`
    functions work in conjunction with one another."""

    data_frame = evaluator_data_set.to_pandas()

    data_set = DataSet.from_pandas(
        data_frame,
        "id",
        description="Lorem Ipsum",
        authors=[Author(name=" ", email="x@x.com", institute=" ")],
    )

    data_frame = data_set.to_pandas()

    data_set = DataSet.from_pandas(
        data_frame,
        "id",
        description="Lorem Ipsum",
        authors=[Author(name=" ", email="x@x.com", institute=" ")],
    )

    evaluator_properties_by_id = {x.id: x for x in evaluator_data_set}

    for entry in data_set.entries:

        evaluator_property = evaluator_properties_by_id[str(entry.id)]
        compare_properties(evaluator_property, entry)


@pytest.mark.parametrize(
    "evaluator_data_set", [simple_evaluator_data_set(), complete_evaluator_data_set()]
)
def test_collection_to_evaluator(evaluator_data_set):
    """A simple test that the `DataSetCollection.to_evaluator` function
    works as expected."""

    data_frame = evaluator_data_set.to_pandas()

    data_set = DataSet.from_pandas(
        data_frame,
        "id",
        description="Lorem Ipsum",
        authors=[Author(name=" ", email="x@x.com", institute=" ")],
    )

    data_set_collection = DataSetCollection(data_sets=[data_set])

    recreated_data_set = data_set_collection.to_evaluator()
    assert len(recreated_data_set) == len(evaluator_data_set)

    evaluator_properties_by_id = {x.id: x for x in evaluator_data_set}

    for recreated_property in recreated_data_set:

        evaluator_property = evaluator_properties_by_id[recreated_property.id]
        compare_evaluator_properties(evaluator_property, recreated_property)


def test_data_set_collection_validation():
    """Check that the data set correctly validates for unique set ids."""

    # Create a set which should not error
    DataSetCollection(data_sets=[create_data_set("data-set-1")])

    # Create a set which should error
    with pytest.raises(ValidationError):

        DataSetCollection(
            data_sets=[create_data_set("data-set-1"), create_data_set("data-set-1")]
        )


def test_molecule_set_collection_validation():
    """Check that the molecule set correctly validates for unique set ids."""

    # Create a set which should not error
    MoleculeSetCollection(molecule_sets=[create_molecule_set("molecule-set-1")])

    # Create a set which should error
    with pytest.raises(ValidationError):

        MoleculeSetCollection(
            molecule_sets=[
                create_molecule_set("molecule-set-1"),
                create_molecule_set("molecule-set-1"),
            ]
        )


def test_molecule_set_validation():
    """Check that the molecule set correctly validates for unique set ids."""

    # Create a set which should not error
    molecule_set = create_molecule_set("molecule-set-1")

    # Create a set which should error
    with pytest.raises(ValidationError):

        molecule_set.entries.append(molecule_set.entries[0])
        MoleculeSet(**molecule_set.dict())
