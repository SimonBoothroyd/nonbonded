import logging

from openff.evaluator import substances, unit
from openff.evaluator.datasets import PhysicalPropertyDataSet, PropertyPhase
from openff.evaluator.properties import Density, SolvationFreeEnergy
from openff.evaluator.thermodynamics import ThermodynamicState

from nonbonded.library.models.authors import Author
from nonbonded.library.models.datasets import (
    Component,
    DataSet,
    DataSetCollection,
    DataSetEntry,
)
from nonbonded.library.utilities.logging import setup_timestamp_logging
from nonbonded.library.utilities.migration import reindex_data_set


def test_reindex_data_set():
    """Tests that the ``reindex_data_set`` function behaves as expected."""

    setup_timestamp_logging(logging.INFO)

    evaluator_data_set = PhysicalPropertyDataSet()

    evaluator_data_set.add_properties(
        Density(
            thermodynamic_state=ThermodynamicState(
                temperature=298.15 * unit.kelvin, pressure=1.0 * unit.atmosphere
            ),
            phase=PropertyPhase.Liquid,
            substance=substances.Substance.from_components("O"),
            value=1.0 * Density.default_unit(),
            uncertainty=1.0 * Density.default_unit(),
        ),
        Density(
            thermodynamic_state=ThermodynamicState(
                temperature=298.15 * unit.kelvin, pressure=1.0 * unit.atmosphere
            ),
            phase=PropertyPhase.Liquid,
            substance=substances.Substance.from_components("C", "O"),
            value=1.0 * Density.default_unit(),
            uncertainty=1.0 * Density.default_unit(),
        ),
        Density(
            thermodynamic_state=ThermodynamicState(
                temperature=300.0 * unit.kelvin, pressure=1.0 * unit.atmosphere
            ),
            phase=PropertyPhase.Liquid,
            substance=substances.Substance.from_components("C", "O"),
            value=1.0 * Density.default_unit(),
            uncertainty=1.0 * Density.default_unit(),
        ),
    )

    data_set = DataSet(
        id="data-set",
        description=" ",
        authors=[Author(name=" ", email="x@x.com", institute=" ")],
        entries=[
            DataSetEntry(
                id=1,
                property_type="Density",
                temperature=298.15,
                pressure=101.325,
                value=1.0,
                std_error=1.0,
                doi=" ",
                components=[
                    Component(smiles="O", mole_fraction=0.5),
                    Component(smiles="C", mole_fraction=0.5),
                ],
            ),
            DataSetEntry(
                id=2,
                property_type="Density",
                temperature=298.15,
                pressure=101.325,
                value=1.0,
                std_error=1.0,
                doi=" ",
                components=[Component(smiles="O", mole_fraction=1.0)],
            ),
        ],
    )

    un_indexed_id = evaluator_data_set.properties[2].id

    reindex_data_set(evaluator_data_set, data_set)

    assert evaluator_data_set.properties[0].id == "2"
    assert evaluator_data_set.properties[1].id == "1"
    assert evaluator_data_set.properties[2].id == un_indexed_id

    data_set_collection = DataSetCollection(
        data_sets=[
            DataSet(
                id="0",
                description=" ",
                authors=[Author(name=" ", email="x@x.com", institute=" ")],
                entries=[
                    DataSetEntry(
                        id=3,
                        property_type="Density",
                        temperature=298.15,
                        pressure=101.325,
                        value=1.0,
                        std_error=1.0,
                        doi=" ",
                        components=[
                            Component(smiles="O", mole_fraction=0.5),
                            Component(smiles="C", mole_fraction=0.5),
                        ],
                    )
                ],
            ),
            DataSet(
                id="1",
                description=" ",
                authors=[Author(name=" ", email="x@x.com", institute=" ")],
                entries=[
                    DataSetEntry(
                        id=4,
                        property_type="Density",
                        temperature=298.15,
                        pressure=101.325,
                        value=1.0,
                        std_error=1.0,
                        doi=" ",
                        components=[Component(smiles="O", mole_fraction=1.0)],
                    )
                ],
            ),
        ]
    )

    reindex_data_set(evaluator_data_set, data_set_collection)

    assert evaluator_data_set.properties[0].id == "4"
    assert evaluator_data_set.properties[1].id == "3"
    assert evaluator_data_set.properties[2].id == un_indexed_id


def test_reindex_data_set_no_mole_fraction():
    """Tests that the ``reindex_data_set`` function behaves as expected
    when exact amounts are present."""

    setup_timestamp_logging(logging.INFO)

    substance = substances.Substance()
    substance.add_component(
        substances.Component(smiles="O"), amount=substances.MoleFraction(1.0)
    )
    substance.add_component(
        substances.Component(smiles="CO", role=substances.Component.Role.Solute),
        amount=substances.ExactAmount(1),
    )

    evaluator_data_set = PhysicalPropertyDataSet()

    evaluator_data_set.add_properties(
        SolvationFreeEnergy(
            thermodynamic_state=ThermodynamicState(
                temperature=298.15 * unit.kelvin, pressure=1.0 * unit.atmosphere
            ),
            phase=PropertyPhase.Liquid,
            substance=substance,
            value=1.0 * SolvationFreeEnergy.default_unit(),
            uncertainty=1.0 * SolvationFreeEnergy.default_unit(),
        ),
    )

    data_set = DataSet(
        id="data-set",
        description=" ",
        authors=[Author(name=" ", email="x@x.com", institute=" ")],
        entries=[
            DataSetEntry(
                id=1,
                property_type="SolvationFreeEnergy",
                temperature=298.15,
                pressure=101.325,
                value=1.0,
                std_error=1.0,
                doi=" ",
                components=[
                    Component(smiles="O", mole_fraction=1.0),
                    Component(
                        smiles="CO", mole_fraction=0.0, exact_amount=1, role="Solute"
                    ),
                ],
            )
        ],
    )

    reindex_data_set(evaluator_data_set, data_set)
    assert evaluator_data_set.properties[0].id == "1"
