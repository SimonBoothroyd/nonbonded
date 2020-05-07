import urllib.parse
from typing import List, Optional, Tuple

import numpy
from pydantic import Field, PositiveInt, validator

from nonbonded.library.models import BaseORM
from nonbonded.library.models.environments import ChemicalEnvironment


class Substance(BaseORM):

    smiles: Tuple[str, ...] = Field(
        ..., description="The SMILES representations of the molecules in a substance."
    )

    def to_url_string(self):
        return urllib.parse.quote(".".join(sorted(self.smiles)))

    @classmethod
    def from_url_string(cls, url_string):

        smiles = urllib.parse.unquote(url_string)
        smiles_tuple = tuple(sorted(smiles.split(".")))

        return Substance(smiles=smiles_tuple)

    def __eq__(self, other):
        return (
            type(other) == Substance and self.to_url_string() == other.to_url_string()
        )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(tuple(sorted(self.smiles)))


class StatePoint(BaseORM):

    temperature: float = Field(..., description="The temperature of the state (K).")
    pressure: float = Field(..., description="The pressure of the state (kPa).")

    mole_fractions: Tuple[float, ...] = Field(
        ..., description="The composition of the state."
    )

    @classmethod
    @validator("temperature")
    def temperature_validator(cls, value):
        assert value >= 0.0
        return value

    @classmethod
    @validator("pressure")
    def pressure_validator(cls, value):
        assert value >= 0.0
        return value

    @classmethod
    @validator("mole_fractions")
    def mole_fractions_validator(cls, value):

        assert len(value) > 0
        assert all(x > 0.0 for x in value)

        assert numpy.isclose(sum(value), 1.0)

        return value


class TargetProperty(BaseORM):

    property_type: str = Field(..., description="The type of property being targeted.")

    n_components: Optional[PositiveInt] = Field(
        None,
        description="The number of components that the property should have been "
        "collected for (e.g. a pure or binary system)",
    )

    target_states: List[StatePoint] = Field(
        ...,
        description="The target states to include in the data set for this class of "
        "property.",
    )


class TargetDataSet(BaseORM):

    target_properties: List[TargetProperty] = Field(
        ..., description="The types of properties incorporated into this data set."
    )
    chemical_environments: List[ChemicalEnvironment] = Field(
        ..., description="The chemical environments incorporated into this data set."
    )


class DataSetValue(BaseORM):

    property_type: str = Field(
        ..., description="The type of property that this value corresponds to."
    )
    state_point: StatePoint = Field(
        ..., description="The state point that this value corresponds to."
    )

    value: float = Field(
        ..., description="The value in the default units of the property type."
    )
    std_error: Optional[float] = Field(
        ...,
        description="The uncertainty in the value in the default units of the "
        "property type. ",
    )


class DataSetEntry(BaseORM):

    substance: Substance = Field(
        ..., description="The substance associated with this entry."
    )
    chemical_environments: List[ChemicalEnvironment] = Field(
        ..., description="The chemical environments present in this entry."
    )
    property_entries: List[DataSetValue] = Field(
        ..., description="The values associated with this entry."
    )


class SelectedDataSet(BaseORM):

    data_entries: List[DataSetEntry] = Field(
        ..., description="The entries in the selected data set."
    )
