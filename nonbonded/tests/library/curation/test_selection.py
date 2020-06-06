import numpy
import pandas
import pytest

from nonbonded.library.curation.components.selection import (
    SelectDataPoints,
    SelectDataPointsSchema,
    State,
    TargetState,
)
from nonbonded.library.models.authors import Author
from nonbonded.library.models.datasets import Component, DataSet, DataSetEntry


@pytest.fixture(scope="module")
def data_frame() -> pandas.DataFrame:

    temperatures = [303.15, 298.15]
    property_types = ["Density", "EnthalpyOfVaporization"]

    data_set = DataSet(
        id="data-set-1",
        description=" ",
        authors=[Author(name=" ", email="x@x.com", institute=" ")],
        entries=[],
    )

    for temperature in temperatures:
        for property_type in property_types:

            data_set.entries.append(
                DataSetEntry(
                    property_type=property_type,
                    temperature=temperature,
                    pressure=101.325,
                    value=1.0,
                    std_error=1.0,
                    doi=" ",
                    components=[Component(smiles="C", mole_fraction=1.0)],
                )
            ),

            data_set.entries.append(
                DataSetEntry(
                    property_type=property_type,
                    temperature=temperature + numpy.random.normal(0.0, 0.1),
                    pressure=101.325,
                    value=1.0,
                    std_error=1.0,
                    doi=" ",
                    components=[Component(smiles="C", mole_fraction=1.0)],
                )
            )

    data_frame = data_set.to_pandas()
    return data_frame


@pytest.mark.parametrize(
    "target_temperatures, expected_temperatures",
    [([300.0], [298.15]), ([301.0], [303.15]), ([300.0, 301.0], [298.15, 303.15])],
)
def test_select_data_points(target_temperatures, expected_temperatures, data_frame):
    """Tests that data points are selected in a reasonably optimal way."""

    states = [
        State(temperature=target_temperature, pressure=101.325, mole_fractions=(1.0,))
        for target_temperature in target_temperatures
    ]

    # Define target states for ambient conditions
    schema = SelectDataPointsSchema(
        target_states=[
            TargetState(
                property_types=[("Density", 1), ("EnthalpyOfVaporization", 1)],
                states=states,
            )
        ]
    )

    selected_data = SelectDataPoints.apply(data_frame, schema)

    assert len(selected_data) == len(expected_temperatures) * 2
    assert len(selected_data["Temperature (K)"].unique()) == len(expected_temperatures)

    selected_temperatures = sorted(selected_data["Temperature (K)"].unique())
    expected_temperatures = sorted(expected_temperatures)

    assert numpy.allclose(selected_temperatures, expected_temperatures)
