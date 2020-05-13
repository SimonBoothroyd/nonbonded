"""A collection of models which outline the scope and options of a particular project.
"""
from typing import List, Optional

from pydantic import Field

from nonbonded.library.models import BaseORM
from nonbonded.library.models.authors import Author
from nonbonded.library.models.forcebalance import ForceBalanceOptions
from nonbonded.library.models.forcefield import SmirnoffParameter


class Optimization(BaseORM):

    id: str = Field(
        ..., description="The unique id assigned to this optimization."
    )
    study_id: str = Field(
        ..., description="The id of the parent study."
    )
    project_id: Optional[str] = Field(
        ..., description="The id of the parent project."
    )

    name: str = Field(..., description="The name of the optimization.")
    description: str = Field(..., description="A description of this optimization.")

    training_set_id: Optional[str] = Field(
        None,
        description="The unique identifier of the data set to use as part of the "
        "optimization.",
    )

    initial_force_field: str = Field(
        ...,
        description="The file name of the force field which will be used as "
        "the starting point for all optimizations. Currently this must be the name "
        "of a force field in the `openforcefields` GitHub repository.",
    )

    parameters_to_train: List[SmirnoffParameter] = Field(
        ..., description="The force field parameters to be optimized."
    )
    force_balance_input: ForceBalanceOptions = Field(
        default_factory=ForceBalanceOptions,
        description="The inputs to use for the optimization.",
    )

    # denominators: Dict[str, str] = Field(
    #     ...,
    #     description="The denominators to scale each class of properties "
    #     "contribution to the objective function by.",
    # )
    # priors: Dict[str, float] = Field(
    #     ..., description="The priors to place on each class of parameter."
    # )


class OptimizationCollection(BaseORM):

    optimizations: List[Optimization] = Field(
        default_factory=list, description="A collection of optimizations.",
    )


class Benchmark(BaseORM):

    id: str = Field(
        ..., description="The unique id assigned to this benchmark."
    )
    study_id: str = Field(
        ..., description="The id of the parent study."
    )
    project_id: str = Field(
        ..., description="The id of the parent project."
    )

    name: str = Field(..., description="The name of the benchmark.")
    description: str = Field(..., description="A description of this benchmark.")

    test_set_id: Optional[str] = Field(
        None,
        description="The unique identifier of the data set to use as part of the "
        "benchmarking.",
    )

    optimization_id: Optional[str] = Field(
        ...,
        description="The unique id of the optimization which should be benchmarked."
        "This option is mutually exclusive with `force_field_name`.",
    )
    force_field_name: Optional[str] = Field(
        ...,
        description="The file name of the force field to use in the benchmark. "
        "Currently this must be the name of a force field in the `openforcefields` "
        "GitHub repository. This option is mutually exclusive with `optimized_id`.",
    )


class BenchmarkCollection(BaseORM):

    benchmarks: List[Benchmark] = Field(
        default_factory=list, description="A collection of benchmarks.",
    )


class Study(BaseORM):

    id: str = Field(..., description="The unique id assigned to this study.")
    project_id: str = Field(
        ..., description="The id of the parent project."
    )

    name: str = Field(..., description="The name of the study.")
    description: str = Field(..., description="A description of this study.")

    optimizations: List[Optimization] = Field(
        default_factory=list,
        description="The optimizations to perform as part of this study."
    )
    benchmarks: List[Benchmark] = Field(
        default_factory=list,
        description="The benchmarks to perform as part of this study."
    )


class StudyCollection(BaseORM):

    studies: List[Study] = Field(
        default_factory=list, description="A collection of studies.",
    )


class Project(BaseORM):

    id: str = Field(..., description="The unique id assigned to the project.")

    name: str = Field(..., description="The name of the project.")
    description: str = Field(..., description="A description of the project.")
    authors: List[Author] = Field(..., description="The authors of the project.")

    studies: List[Study] = Field(
        default_factory=list,
        description="The studies conducted as part of the project."
    )


class ProjectCollection(BaseORM):

    projects: List[Project] = Field(
        default_factory=list, description="A collection of projects.",
    )
