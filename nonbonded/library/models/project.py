from typing import List

from pydantic import BaseModel, Field

from nonbonded.library.models.data import DataSetDefinition


class Author(BaseModel):

    name: str = Field(..., description="The full name of the author.")
    email: str = Field(..., description="The author's email address.")
    institute: str = Field(..., description="The author's host institute.")


class Optimization(BaseModel):

    title: str = Field(..., description="The title of the optimization.")
    description: str = Field(
        ..., description="A description of this optimization.",
    )

    training_set: DataSetDefinition = Field(
        ..., description="A description of the data set to optimise against.",
    )


class Study(BaseModel):

    title: str = Field(..., description="The title of the study.")
    description: str = Field(
        ..., description="A description of this study.",
    )

    optimizations: List[Optimization] = Field(
        ..., description="The optimizations to perform as part of this study."
    )
    test_set: DataSetDefinition = Field(
        ...,
        description="A description of the composition of the data set benchmark "
        "against.",
    )


class Project(BaseModel):

    identifier: str = Field(
        ...,
        description="The unique id assigned to the project. "
        "This must be a valid file name.",
    )

    title: str = Field(..., description="The title of the project.")
    abstract: str = Field(..., description="The project's abstract.")
    authors: List[Author] = Field(..., description="The authors of the project.")

    studies: List[Study] = Field(
        ..., description="The studies conducted as part of the project."
    )
