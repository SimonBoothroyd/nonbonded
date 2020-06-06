import numpy
import pandas
import pytest

from nonbonded.library.curation.components.filtering import (
    FilterByPressureSchema,
    FilterByTemperatureSchema,
)
from nonbonded.library.curation.workflow import Workflow, WorkflowSchema
from nonbonded.library.models.authors import Author
from nonbonded.library.models.datasets import Component, DataSet, DataSetEntry


@pytest.fixture(scope="module")
def data_frame() -> pandas.DataFrame:

    data_set = DataSet(
        id="data-set-1",
        description=" ",
        authors=[Author(name=" ", email="x@x.com", institute=" ")],
        entries=[
            DataSetEntry(
                property_type="Density",
                temperature=298.15,
                pressure=101.325,
                value=1.0,
                std_error=1.0,
                doi=" ",
                components=[Component(smiles="C", mole_fraction=1.0)],
            ),
            DataSetEntry(
                property_type="Density",
                temperature=305.15,
                pressure=101.325,
                value=1.0,
                std_error=1.0,
                doi=" ",
                components=[Component(smiles="C", mole_fraction=1.0)],
            ),
            DataSetEntry(
                property_type="Density",
                temperature=298.15,
                pressure=105.325,
                value=1.0,
                std_error=1.0,
                doi=" ",
                components=[Component(smiles="C", mole_fraction=1.0)],
            ),
        ],
    )

    return data_set.to_pandas()


def test_workflow(data_frame):
    """Test that a simple workflow can be applied to a data set."""

    schema = WorkflowSchema(
        component_schemas=[
            FilterByTemperatureSchema(
                minimum_temperature=290.0, maximum_temperature=300.0
            ),
            FilterByPressureSchema(minimum_pressure=101.3, maximum_pressure=101.4),
        ]
    )

    filtered_frame = Workflow.apply(data_frame, schema)
    assert len(filtered_frame) == 1

    assert numpy.isclose(filtered_frame["Temperature (K)"].values[0], 298.15)
    assert numpy.isclose(filtered_frame["Pressure (kPa)"].values[0], 101.325)
