"""A set of utilities for manipulating pandas data frames created
using the Evaluator framework.
"""
from typing import List

import pandas

from nonbonded.library.models.datasets import (
    DataSet,
    DataSetEntry,
    StatePoint,
    Substance,
)


def data_frame_to_entries(
    data_frame: pandas.DataFrame,
) -> List[DataSetEntry]:

    property_headers = [x for x in data_frame if " Value " in x]

    data_entries = []

    for property_header in property_headers:

        property_frame = data_frame.dropna(subset=[property_header])

        if len(data_frame) == 0:
            continue

        property_name = property_header.split(" ")[0]

        for _, row in property_frame.iterrows():

            n_components = row["N Components"]

            column_names = [f"Component {i + 1}" for i in range(n_components)]
            mole_fractions = [
                row[f"Mole Fraction {i + 1}"] for i in range(n_components)
            ]

            components = tuple(sorted(row[x] for x in column_names))
            substance = Substance(smiles=components)

            value = row[property_header]
            uncertainty = row[property_header.replace("Value", "Uncertainty")]

            temperature = row["Temperature (K)"]
            pressure = row["Pressure (kPa)"]

            state_point = StatePoint(
                temperature=temperature,
                pressure=pressure,
                mole_fractions=tuple(mole_fractions),
            )

            data_set_entry = DataSetEntry(
                property_type=property_name,
                state_point=state_point,
                value=value,
                std_error=uncertainty,
                doi="Source",
                substance=substance
            )

            data_entries.append(data_set_entry)

    return data_entries
