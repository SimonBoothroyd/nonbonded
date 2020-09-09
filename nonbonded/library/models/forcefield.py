from typing import TYPE_CHECKING, List, Union

from pydantic import Field

from nonbonded.library.models import BaseORM
from nonbonded.library.models.validators.string import NonEmptyStr

if TYPE_CHECKING:
    from openff.evaluator.forcefield import ForceFieldSource
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

    def __eq__(self, other: "Parameter"):
        return (
            type(self) == type(other)
            and self.handler_type == other.handler_type
            and self.smirks == other.smirks
            and self.attribute_name == other.attribute_name
        )

    def __hash__(self):
        return hash((self.handler_type, self.smirks, self.attribute_name))


class ForceField(BaseORM):

    inner_content: NonEmptyStr = Field(
        ...,
        description="The string representation of a set of force field parameters."
        "This should either be an OpenFF SMIRNOFF representation, or an "
        "OpenFF Evaluator JSON serialized `ForceFieldSource`.",
    )

    @classmethod
    def from_openff(
        cls, force_field: Union["OpenForceField", "ForceFieldSource"]
    ) -> "ForceField":

        from openff.evaluator.forcefield import ForceFieldSource
        from openforcefield.typing.engines.smirnoff.forcefield import (
            ForceField as OpenForceField,
        )

        if isinstance(force_field, OpenForceField):

            return ForceField(
                inner_content=force_field.to_string(discard_cosmetic_attributes=True)
            )

        elif isinstance(force_field, ForceFieldSource):

            return ForceField(inner_content=force_field.json())

        else:
            raise NotImplementedError()

    def to_openff(self) -> Union["OpenForceField", "ForceFieldSource"]:

        from openff.evaluator.forcefield import ForceFieldSource
        from openforcefield.typing.engines.smirnoff.forcefield import ForceField

        try:
            force_field = ForceField(self.inner_content)
        except (TypeError, IOError):
            force_field = ForceFieldSource.parse_json(self.inner_content)

        return force_field


class ForceFieldCollection(BaseORM):

    force_fields: List[ForceField] = Field(
        default_factory=list, description="A collection of force fields"
    )
