from typing import List, Tuple, Union

import numpy
import pandas
from pydantic import BaseModel, Field, validator

from nonbonded.library.curation.components import Component, ComponentSchema
from nonbonded.library.utilities.pandas import reorder_data_frame

PropertyType = Tuple[str, int]


class State(BaseModel):

    temperature: float = Field(..., description="The temperature (K) of interest.")
    pressure: float = Field(..., description="The pressure (kPa) of interest.")

    mole_fractions: Tuple[float, ...] = Field(
        ..., description="The composition of interest."
    )


class TargetState(BaseModel):

    property_types: List[PropertyType] = Field(
        ..., description="The properties to select at the specified states."
    )
    states: List[State] = Field(
        ..., description="The states at which data points should be selected."
    )

    @classmethod
    @validator("property_types")
    def property_types_validator(cls, value):

        assert len(value) > 0
        n_components = value[0][1]

        assert all(x[1] == n_components for x in value)
        return value


class SelectDataPointsSchema(ComponentSchema):

    target_states: List[TargetState] = Field(
        ...,
        description="A list of the target states for which we would ideally include "
        "data points for (e.g. density data points measured at ambient conditions, or "
        "for density AND enthalpy of mixing measurements made for systems with a "
        "roughly 50:50 composition).",
    )


class SelectDataPoints(Component[SelectDataPointsSchema]):
    """The method attempts to find a set of data points for each substance
    in a data set which are clustered around the set of conditions specified
    in the ``target_states`` input array.

    The points will be chosen so as to try and maximise the number of
    properties measured at the same condition (e.g. ideally we would
    have a data point for each property at T=298.15 and p=1atm) as this
    will maximise the chances that we can extract all properties from a
    single simulation.
    """

    @classmethod
    def _property_header(cls, data_frame, property_type):

        for column in data_frame:

            if column.find(f"{property_type} Value") < 0:
                continue

            return column

        return None

    @classmethod
    def _distances_to_cluster(cls, data_frame, target_state):

        n_components = target_state.property_types[0][1]
        distances_sqr = pandas.DataFrame()

        for index, state_point in enumerate(target_state.states):

            distance_sqr = (
                (data_frame["Temperature (K)"] - state_point.temperature) ** 2
                + (data_frame["Pressure (kPa)"] / 10.0 - state_point.pressure / 10.0)
                ** 2
            )

            for component_index in range(n_components):
                distance_sqr += (
                    data_frame[f"Mole Fraction {component_index + 1}"]
                    - state_point.mole_fractions[component_index]
                ) ** 2

            distances_sqr[index] = distance_sqr

        return distances_sqr

    @classmethod
    def _select_substance_data_points(cls, original_data_frame, target_state):

        n_components = target_state.property_types[0][1]

        data_frame = original_data_frame[
            original_data_frame["N Components"] == n_components
        ].copy()
        data_frame["Property Type"] = ""

        property_types = [x[0] for x in target_state.property_types]

        for property_type in property_types:
            property_header = cls._property_header(data_frame, property_type)
            data_frame.loc[
                data_frame[property_header].notna(), "Property Type"
            ] = property_type

        data_frame["Temperature (K)"] = data_frame["Temperature (K)"].round(2)
        data_frame["Pressure (kPa)"] = data_frame["Pressure (kPa)"].round(1)

        for index in range(n_components):
            data_frame[f"Mole Fraction {index + 1}"] = data_frame[
                f"Mole Fraction {index + 1}"
            ].round(3)

        # Compute the distance to each cluster
        distances = cls._distances_to_cluster(data_frame, target_state)
        data_frame["Cluster"] = distances.idxmin(axis=1)

        cluster_headers = [
            "Temperature (K)",
            "Pressure (kPa)",
            *[f"Mole Fraction {index + 1}" for index in range(n_components)],
        ]

        grouped_data = data_frame.groupby(
            by=[*cluster_headers, "Cluster"], as_index=False,
        ).agg({"Property Type": pandas.Series.nunique})

        selected_data = [False] * len(data_frame)

        for cluster_index in range(len(target_state.states)):

            cluster_data = grouped_data[grouped_data["Cluster"] == cluster_index]

            if len(cluster_data) == 0:
                continue

            open_list = [x[0] for x in target_state.property_types]

            while len(open_list) > 0 and len(cluster_data) > 0:

                largest_cluster_index = cluster_data["Property Type"].idxmax(axis=0)

                select_data = data_frame["Property Type"].isin(open_list)

                for cluster_header in cluster_headers:
                    select_data = select_data & numpy.isclose(
                        data_frame[cluster_header],
                        cluster_data.loc[largest_cluster_index, cluster_header],
                    )

                selected_data = selected_data | select_data

                for property_type in data_frame[select_data]["Property Type"].unique():
                    open_list.remove(property_type)

                cluster_data = cluster_data.drop(largest_cluster_index)

        return original_data_frame[selected_data]

    @classmethod
    def _apply(
        cls, data_frame: pandas.DataFrame, schema: SelectDataPointsSchema, n_processes
    ) -> pandas.DataFrame:

        max_n_substances = data_frame["N Components"].max()
        component_headers = [f"Component {i + 1}" for i in range(max_n_substances)]

        # Re-order the data frame so that the components are alphabetically sorted.
        # This will make it easier to find unique substances.
        ordered_data_frame = reorder_data_frame(data_frame)

        # Find all of the unique substances in the data frame.
        unique_substances = ordered_data_frame[component_headers].drop_duplicates()

        selected_data = []

        # Start to choose the state points for each unique substance.
        for _, unique_substance in unique_substances.iterrows():

            substance_data_frame = ordered_data_frame

            for index, component in enumerate(unique_substance[component_headers]):

                substance_data_frame = substance_data_frame[
                    substance_data_frame[component_headers[index]] == component
                ]

            for target_state in schema.target_states:

                substance_selected_data = cls._select_substance_data_points(
                    substance_data_frame, target_state
                )

                if len(substance_selected_data) == 0:
                    continue

                selected_data.append(substance_selected_data)

        selected_data = pandas.concat(selected_data, ignore_index=True, sort=False)
        return selected_data


SelectionComponentSchema = Union[SelectDataPointsSchema]
