from typing import TYPE_CHECKING, List

from pydantic import Field

from nonbonded.library.models import BaseORM
from nonbonded.library.models.validators.string import NonEmptyStr

if TYPE_CHECKING:
    from openforcefield.typing.engines.smirnoff.forcefield import (
        ForceField as OpenForceField,
    )


class Parameter(BaseORM):

    handler_type: NonEmptyStr = Field(
        ...,
        description="The type of the parameter handler associated with this "
        "parameter.",
    )

    smirks: NonEmptyStr = Field(
        ..., description="The smirks identifier of the parameter."
    )

    attribute_name: NonEmptyStr = Field(
        ..., description="The attribute name associated with the parameter."
    )


class ForceField(BaseORM):

    inner_content: NonEmptyStr = Field(
        ...,
        description="The xml representation of a force field in the SMIRNOFF "
        "force field format",
    )

    @classmethod
    def from_openff(cls, force_field: "OpenForceField") -> "ForceField":

        return ForceField(
            inner_content=force_field.to_string(discard_cosmetic_attributes=True)
        )

    def to_openff(self) -> "OpenForceField":

        from openforcefield.typing.engines.smirnoff.forcefield import ForceField

        force_field = ForceField(self.inner_content)

        return force_field


class ForceFieldCollection(BaseORM):

    force_fields: List[ForceField] = Field(
        default_factory=list, description="A collection of force fields"
    )
