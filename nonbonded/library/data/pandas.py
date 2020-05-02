"""A set of utilities for manipulating pandas data frames created
using the Evaluator framework.
"""
from collections import defaultdict

import pandas

from nonbonded.library.models.data import (
    DataSetSubstance,
    DataSetSummary,
    PropertyType,
    Substance,
    SubstanceType,
)
from nonbonded.library.utilities.checkmol import analyse_functional_groups


def data_frame_to_summary(data_frame: pandas.DataFrame) -> DataSetSummary:

    property_headers = [x for x in data_frame if " Value " in x]

    properties_per_substance = defaultdict(set)

    for property_header in property_headers:

        property_frame = data_frame.dropna(subset=[property_header])

        if len(data_frame) == 0:
            continue

        property_name = property_header.split(" ")[0]

        for _, row in property_frame.iterrows():

            n_components = row["N Components"]

            column_names = [*[f"Component {i + 1}" for i in range(n_components)]]

            components = tuple(sorted(row[x] for x in column_names))

            substance = Substance(smiles=components)

            substance_type = SubstanceType.from_n_components(n_components)
            property_type = PropertyType(
                property_class=property_name, substance_type=substance_type
            )

            properties_per_substance[substance].add(property_type)

    data_set_substances = []

    for substance, property_types in properties_per_substance.items():

        chemical_environments = set()

        for smiles in substance.smiles:

            smiles_environments = analyse_functional_groups(smiles)

            if smiles_environments is None:
                smiles_environments = {}

            chemical_environments.update(smiles_environments)

        chemical_environments = [*chemical_environments]
        property_types = [*property_types]

        data_set_substance = DataSetSubstance(
            components=substance,
            property_types=property_types,
            chemical_environments=chemical_environments,
        )

        data_set_substances.append(data_set_substance)

    data_set_summary = DataSetSummary(
        n_data_points=len(data_frame), substances=data_set_substances
    )

    return data_set_summary
