from pydantic import Field

from nonbonded.library.models import BaseORM


class CondaEnvironment(BaseORM):

    yaml: str = Field(
        ..., description="The yaml representation of a conda environment."
    )
