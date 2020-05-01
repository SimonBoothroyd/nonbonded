from enum import Enum
from typing import List, Tuple

import numpy
from pydantic import BaseModel, Field, validator


class ChemicalEnvironment(Enum):

    Hydroxy = "027"
    Alcohol = "028"
    Caboxylic_acid = "076"
    Ester = "078"
    Ether = "037"
    Aldehyde = "004"
    Ketone = "005"
    Thiocarbonyl = "006"
    Phenol = "034"
    Amine = "047"
    Halogenated = "061"
    Amide = "080"
    Nitro = "150"
    Alkene = "199"
    Aromatic = "201"
    Heterocycle = "202"


class SubstanceType(Enum):

    Pure = "Pure"
    Binary = "Binary"


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


class PropertyDefinition(BaseModel):

    property_type: str
    composition: SubstanceType = Field(
        ..., description="The type of substances chosen for this class of property."
    )

    target_states: List[StatePoint] = Field(
        ...,
        description="The target states to include in the data set for this class of "
        "property.",
    )


class DataSetDefinition(BaseModel):

    property_definitions: List[PropertyDefinition] = Field(
        ..., description="The types of properties incorporated into this data set."
    )
    chemical_environments: List[ChemicalEnvironment] = Field(
        ..., description="The chemical environments incorporated into this data set."
    )
