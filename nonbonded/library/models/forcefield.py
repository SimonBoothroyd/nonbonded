from typing import List

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


class ForceField(BaseORM):

    inner_xml: str = Field(
        ...,
        description="The xml representation of a force field in the SMIRNOFF "
        "force field format",
    )


class ForceFieldCollection(BaseORM):

    force_fields: List[ForceField] = Field(
        default_factory=list, description="A collection of force fields"
    )
