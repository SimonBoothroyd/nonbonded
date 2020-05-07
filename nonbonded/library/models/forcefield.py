from pydantic import BaseModel, Field


class SmirnoffParameter(BaseModel):

    handler_type: str = Field(
        ...,
        description="The type of the parameter handler associated with this "
        "parameter.",
    )

    smirks: str = Field(..., description="The smirks identifier of the parameter.")

    attribute_name: str = Field(
        ..., description="The attribute name associated with the parameter."
    )
