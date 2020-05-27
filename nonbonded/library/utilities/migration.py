from typing import TYPE_CHECKING

from nonbonded.library.models.datasets import DataSet
from nonbonded.library.utilities.pandas import reorder_data_frame

if TYPE_CHECKING:

    from openff.evaluator.client import RequestResult
    from openff.evaluator.datasets import PhysicalPropertyDataSet


def reindex_data_set(data_set: "PhysicalPropertyDataSet", reference_set: DataSet):
    """Attempts to change the unique id of estimated estimated data points to match
    the unique id of their corresponding reference data points based upon the state
    at which they were measured.

    **Note**: the data set will be modified in place.

    This method should **only** be used when attempting to convert previous results
    into the new framework, and not in general.

    Parameters
    ----------
    data_set: PhysicalPropertyDataSet
        The data set to re-index.
    reference_set: DataSet
        The data set whose ids should be matched.
    """

    import pandas

    if len(data_set) == 0:
        return

    estimated_data_frame = reorder_data_frame(data_set.to_pandas())
    reference_data_frame = reorder_data_frame(reference_set.to_pandas())

    minimum_n_components = estimated_data_frame["N Components"].min()
    maximum_n_components = estimated_data_frame["N Components"].max()

    id_mappings = []

    property_headers = [x for x in estimated_data_frame if x.find(" Value ") >= 0]

    for n_components in range(minimum_n_components, maximum_n_components + 1):

        for property_header in property_headers:

            estimated_component_data = estimated_data_frame[
                estimated_data_frame["N Components"] == n_components
            ]
            reference_component_data = reference_data_frame[
                reference_data_frame["N Components"] == n_components
            ]

            estimated_component_data = estimated_component_data[
                estimated_component_data[property_header].notna()
            ].copy()
            reference_component_data = reference_component_data[
                reference_component_data[property_header].notna()
            ].copy()

            if len(estimated_component_data) == 0 or len(reference_component_data) == 0:
                continue

            component_data_frames = [estimated_component_data, reference_component_data]

            comparison_columns = {"Temperature (K)", "Pressure (kPa)", "Phase"}

            for component_data in component_data_frames:

                component_data["Temperature (K)"] = component_data[
                    "Temperature (K)"
                ].round(1)
                component_data["Pressure (kPa)"] = component_data[
                    "Pressure (kPa)"
                ].round(1)

                for index in range(n_components):

                    component_data[f"Mole Fraction {index + 1}"] = component_data[
                        f"Mole Fraction {index + 1}"
                    ].round(2)

                    comparison_columns.update(
                        [
                            f"Component {index + 1}",
                            f"Role {index + 1}",
                            f"Mole Fraction {index + 1}",
                        ]
                    )

            comparison_columns = [*comparison_columns]

            joined_frames = pandas.merge(
                estimated_component_data,
                reference_component_data,
                on=comparison_columns,
                suffixes=("_orig", "_new"),
            )

            joined_frames.drop_duplicates(inplace=True)

            assert len(joined_frames) == len(estimated_component_data)
            id_mappings.append(joined_frames[["Id_orig", "Id_new"]])

    id_mappings_frame = pandas.concat(id_mappings, ignore_index=True, sort=False)

    id_mappings = {x["Id_orig"]: x["Id_new"] for _, x in id_mappings_frame.iterrows()}

    for physical_property in data_set:
        physical_property.id = f"{id_mappings[physical_property.id]}"


def reindex_results(request_results: "RequestResult", reference_set: DataSet):

    """Attempts to change the unique id of (un)estimated estimated data points to match
    the unique id of their corresponding reference data points based upon the state
    at which they were measured.

    **Note**: the request results object will be modified in place.

    This method should **only** be used when attempting to convert previous results
    into the new framework, and not in general.

    Parameters
    ----------
    request_results: RequestResult
        The results to re-index.
    reference_set: DataSet
        The data set whose ids should be matched.
    """

    reindex_data_set(request_results.estimated_properties, reference_set)
    reindex_data_set(request_results.unsuccessful_properties, reference_set)

    return request_results
