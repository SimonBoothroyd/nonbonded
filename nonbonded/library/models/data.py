import urllib.parse
from enum import Enum
from typing import Dict, List, Tuple

import numpy
from pydantic import BaseModel, Field, validator

from nonbonded.library.models.environments import ChemicalEnvironment


class SubstanceType(Enum):

    Pure = "Pure"
    Binary = "Binary"

    @classmethod
    def from_n_components(cls, n_components):

        if n_components == 1:
            return cls.Pure
        elif n_components == 2:
            return cls.Binary

        raise NotImplementedError()


class PropertyType(BaseModel):

    property_class: str = Field(
        ..., description="The class of property represented by this type."
    )
    substance_type: SubstanceType = Field(
        ..., description="The type of substances chosen for this class of property."
    )

    def __eq__(self, other):
        return (
            type(other) == PropertyType
            and self.property_class == other.property_class
            and self.substance_type == other.substance_type
        )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.property_class, self.substance_type.value))


class Substance(BaseModel):

    smiles: Tuple[str, ...] = Field(
        ..., description="The SMILES representations of the molecules in a substance."
    )

    @validator("smiles")
    def smiles_validator(cls, value):
        return tuple(sorted(value))

    def to_url_string(self):
        return urllib.parse.quote(".".join(self.smiles))

    @classmethod
    def from_url_string(cls, url_string):

        smiles = urllib.parse.unquote(url_string)
        smiles_tuple = tuple(sorted(smiles.split(".")))

        return Substance(smiles=smiles_tuple)

    def __eq__(self, other):
        return type(other) == Substance and self.smiles == other.smiles

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.smiles)


class StatePoint(BaseModel):

    temperature: float = Field(..., description="The temperature of the state (K).")
    pressure: float = Field(..., description="The pressure of the state (kPa).")

    mole_fractions: Tuple[float] = Field(
        ..., description="The composition of the state."
    )

    @validator("temperature")
    def temperature_validator(cls, value):
        assert value >= 0.0
        return value

    @validator("pressure")
    def pressure_validator(cls, value):
        assert value >= 0.0
        return value

    @validator("mole_fractions")
    def mole_fractions_validator(cls, value):

        assert len(value) > 0
        assert all(x > 0.0 for x in value)

        assert numpy.isclose(sum(value), 1.0)

        return value


class TargetProperty(BaseModel):

    property_type: PropertyType = Field("The type of property being targeted.")

    target_states: List[StatePoint] = Field(
        ...,
        description="The target states to include in the data set for this class of "
        "property.",
    )


class TargetDataSet(BaseModel):

    target_properties: List[TargetProperty] = Field(
        ..., description="The types of properties incorporated into this data set."
    )
    chemical_environments: List[ChemicalEnvironment] = Field(
        ..., description="The chemical environments incorporated into this data set."
    )


class DataSetSubstance(BaseModel):

    components: Substance = Field(..., description="The components in this substance.")

    chemical_environments: List[ChemicalEnvironment] = Field(
        ..., description="The chemical environments present in this substance."
    )
    property_types: List[PropertyType] = Field(
        ..., description="The property types for which included for this substance"
    )


class DataSetSummary(BaseModel):

    n_data_points: int = Field(
        ..., description="The total number of data points in the set."
    )

    substances: List[DataSetSubstance] = Field(
        ..., description="The substances present in the data set."
    )
