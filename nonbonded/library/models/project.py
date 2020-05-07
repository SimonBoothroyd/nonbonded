"""A collection of models which outline the scope and
options of a particular project.
"""
from typing import Dict, List

from pydantic import BaseModel, Field

from nonbonded.library.models.datasets import TargetDataSet
from nonbonded.library.models.forcebalance import ForceBalanceOptions
from nonbonded.library.models.forcefield import SmirnoffParameter


class Author(BaseModel):

    name: str = Field(..., description="The full name of the author.")
    email: str = Field(..., description="The author's email address.")
    institute: str = Field(..., description="The author's host institute.")


class Optimization(BaseModel):

    identifier: str = Field(
        ...,
        description="The unique id assigned to the optimization. "
        "This must be a valid file name.",
    )

    title: str = Field(..., description="The title of the optimization.")
    description: str = Field(
        ..., description="A description of this optimization.",
    )

    target_training_set: TargetDataSet = Field(
        ...,
        description="A description of target composition of the optimization "
        "training set.",
    )
    parameters_to_train: List[SmirnoffParameter] = Field(
        ..., description="The force field parameters to be optimized."
    )

    denominators: Dict[str, str] = Field(
        ...,
        description="The denominators to scale each class of properties "
        "contribution to the objective function by.",
    )
    priors: Dict[str, float] = Field(
        ..., description="The priors to place on each class of parameter."
    )


class Study(BaseModel):

    identifier: str = Field(
        ...,
        description="The unique id assigned to the study. "
        "This must be a valid file name and url fragment.",
    )

    title: str = Field(..., description="The title of the study.")
    description: str = Field(
        ..., description="A description of this study.",
    )

    optimizations: List[Optimization] = Field(
        ..., description="The optimizations to perform as part of this study."
    )
    optimization_inputs: ForceBalanceOptions = Field(
        default_factory=ForceBalanceOptions,
        description="The inputs to provide to ForceBalance.",
    )

    target_test_set: TargetDataSet = Field(
        ...,
        description="A description of target composition of the benchmarking test set.",
    )

    initial_force_field: str = Field(
        ...,
        description="The file name of the force field which will be used as "
        "the starting point for all optimizations. Currently this must be the name "
        "of a force field in the `openforcefields` GitHub repository.",
    )


class Project(BaseModel):

    identifier: str = Field(
        ...,
        description="The unique id assigned to the project. "
        "This must be a valid file name and url fragment.",
    )

    title: str = Field(..., description="The title of the project.")
    abstract: str = Field(..., description="The project's abstract.")
    authors: List[Author] = Field(..., description="The authors of the project.")

    studies: List[Study] = Field(
        ..., description="The studies conducted as part of the project."
    )
