from typing import List

import requests
from pydantic import Field

from nonbonded.library.models import BaseORM


class Parameter(BaseORM):

    handler_type: str = Field(
        ...,
        description="The type of the parameter handler associated with this "
        "parameter.",
    )

    smirks: str = Field(..., description="The smirks identifier of the parameter.")

    attribute_name: str = Field(
        ..., description="The attribute name associated with the parameter."
    )


class RefitForceField(BaseORM):

    project_id: str = Field(
        ..., description="The id of the project for which the force field was refit."
    )
    study_id: str = Field(
        ..., description="The id of the study for which the force field was refit."
    )
    optimization_id: str = Field(
        ..., description="The id of the optimization which generated the force field."
    )

    inner_xml: str = Field(
        ...,
        description="The xml representation of a force field in the SMIRNOFF "
        "force field format",
    )


class RefitForceFieldCollection(BaseORM):

    force_fields: List[RefitForceField] = Field(
        default_factory=list, description="A collection of refit force fields"
    )

    @classmethod
    def from_rest(cls) -> "RefitForceFieldCollection":

        force_fields_request = requests.get(
            f"http://localhost:5000/api/v1/forcefields/"
        )
        force_fields_request.raise_for_status()

        force_fields = RefitForceFieldCollection.parse_raw(force_fields_request.text)
        return force_fields
