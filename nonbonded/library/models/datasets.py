from typing import List, Optional

import pandas
from pydantic import Field

from nonbonded.library.models import BaseORM
from nonbonded.library.models.authors import Author


class Component(BaseORM):

    smiles: str = Field(
        ..., description="The smiles representation of the component."
    )
    mole_fraction: float = Field(
        ..., description="The mole fraction of this component."
    )
    exact_amount: int = Field(
        0, description="The exact amount of this component."
    )
    role: str = Field(
        "Solvent",
        description="The role of this component in the system (e.g solvent, solute, "
        "ligand, etc.)"
    )


class DataSetEntry(BaseORM):

    property_type: str = Field(
        ...,
        description="The type of property that this value corresponds to. This should "
        "correspond to an `evaluator.properties` property class name."
    )

    temperature: float = Field(
        ..., description="The temperature (K) at which this value was measured."
    )
    pressure: float = Field(
        ..., description="The pressure (kPa) at which this value was measured."
    )
    phase: str = Field(
        "Liquid", description="The phase that the property was measured in."
    )

    unit: str = Field(
        ..., description="The unit that the `value` and `std_error` is reported in."
    )

    value: float = Field(
        ..., description="The value in units of `unit`."
    )
    std_error: Optional[float] = Field(
        ...,
        description="The std error in units of `unit`",
    )

    doi: str = Field(
        ..., description="The DOI which encodes the source of the measurement."
    )

    components: List[Component] = Field(
        ...,
        description="The components in the systems for which the measurement was made."
    )

    @classmethod
    def from_series(cls, data_row: pandas.Series) -> "DataSetEntry":

        data_row = data_row.dropna()

        property_header = next(
            iter(
                key for key, value in data_row.items() if " Value " in key
            )
        )

        n_components = data_row["N Components"]

        data_entry = cls(
            property_type=property_header.split(" ")[0],
            temperature=data_row["Temperature (K)"],
            pressure=data_row["Pressure (kPa)"],
            phase=data_row["Phase"],
            value=data_row["property_header"],
            std_error=data_row[property_header.replace("Value", "Uncertainty")],
            components=[
                Component(
                    smiles=f"Component {i + 1}",
                    mole_fraction=f"Mole Fraction {i + 1}",
                    exact_amount=f"Exact Amount {i + 1}",
                    role=f"Role {i + 1}"
                )
                for i in range(n_components)
            ],
            doi=data_row["Source"],
        )

        return data_entry

    def to_series(self) -> pandas.Series:

        value_header = f"{self.property_type} Value ({self.unit})"
        std_error_header = f"{self.property_type} Uncertainty ({self.unit})"

        data_row = {
            "Temperature (K)": self.temperature,
            "Pressure (kPa)": self.pressure,
            "Phase": self.phase,
            "N Components": len(self.components),
            value_header: self.value,
            std_error_header: self.std_error,
            "Source": self.doi
        }

        for i, component in enumerate(self.components):

            data_row.update(
                {
                    f"Component {i + 1}": component.smiles,
                    f"Mole Fraction {i + 1}": component.mole_fraction,
                    f"Exact Amount {i + 1}": component.exact_amount,
                    f"Role {i + 1}": component.role
                }
            )

        return pandas.Series(data_row)


class DataSet(BaseORM):

    id: str = Field(
        ..., description="The unique identifier associated with the data set."
    )

    description: str = Field(
        ..., description="A description of why and how this data set was chosen."
    )
    authors: List[Author] = Field(
        ..., description="The authors who prepared the data set."
    )

    entries: List[DataSetEntry] = Field(..., description="The entries in the data set.")

    @classmethod
    def from_pandas(
        cls,
        data_frame: pandas.DataFrame,
        identifier: str,
        description: str,
        authors: List[Author]
    ):

        data_set = cls(
            identifier=identifier,
            description=description,
            authors=authors,
            entries=[
                DataSetEntry.from_series(row) for _, row in data_frame.iterrows()
            ]
        )

        return data_set

    def to_pandas(self) -> pandas.DataFrame:

        data_rows = [entry.to_series() for entry in self.entries]
        data_frame = pandas.DataFrame(data_rows)

        return data_frame


class DataSetCollection(BaseORM):

    data_sets: List[DataSet] = Field(
        default_factory=list, description="A collection of data sets.",
    )
