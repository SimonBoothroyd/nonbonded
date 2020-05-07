"""A set of utilities for manipulating pandas data frames created
using the Evaluator framework.
"""
from collections import defaultdict

import pandas

from nonbonded.library.models.datasets import (
    DataSetEntry,
    SelectedDataSet,
    StatePoint,
    Substance,
)
from nonbonded.library.utilities.checkmol import analyse_functional_groups


def data_frame_to_summary(data_frame: pandas.DataFrame) -> SelectedDataSet:

    property_headers = [x for x in data_frame if " Value " in x]

    properties_per_substance = defaultdict(lambda: defaultdict(list))

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

            temperature = row["Temperature (K)"]
            pressure = row["Pressure (kPa)"]

            state_point = StatePoint(
                temperature=temperature,
                pressure=pressure,
                mole_fractions=tuple(mole_fractions),
            )

            properties_per_substance[substance][property_name].append(state_point)

    data_entries = []

    for substance in properties_per_substance:

        chemical_environments = set()

        for smiles in substance.smiles:

            smiles_environments = analyse_functional_groups(smiles)

            if smiles_environments is None:
                smiles_environments = {}

            chemical_environments.update(smiles_environments)

        chemical_environments = [*chemical_environments]
        property_entries = properties_per_substance[substance]

        data_entry = DataSetEntry(
            substance=substance,
            chemical_environments=chemical_environments,
            property_entries=property_entries,
        )

        data_entries.append(data_entry)

    data_set_summary = SelectedDataSet(
        n_data_points=len(data_frame), data_entries=data_entries
    )

    return data_set_summary
