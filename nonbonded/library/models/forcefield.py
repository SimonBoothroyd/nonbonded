from typing import TYPE_CHECKING, List

from pydantic import Field

from nonbonded.library.models import BaseORM

if TYPE_CHECKING:
    from openforcefield.typing.engines.smirnoff.forcefield import (
        ForceField as OpenForceField,
    )


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

    @classmethod
    def from_openff(cls, force_field: "OpenForceField") -> "ForceField":

        return ForceField(
            inner_xml=force_field.to_string(discard_cosmetic_attributes=True)
        )

    def to_openff(self) -> "OpenForceField":

        from openforcefield.typing.engines.smirnoff.forcefield import ForceField

        force_field = ForceField(self.inner_xml)

        return force_field


class ForceFieldCollection(BaseORM):

    force_fields: List[ForceField] = Field(
        default_factory=list, description="A collection of force fields"
    )
