from pydantic import Field
from pydantic.main import BaseModel


class CondaEnvironment(BaseModel):

    yaml: str = Field(
        ..., description="The yaml representation of a conda environment."
    )
