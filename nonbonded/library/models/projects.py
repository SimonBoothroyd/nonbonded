"""A collection of models which outline the scope and options of a particular project.
"""
from typing import TYPE_CHECKING, Dict, List, Optional

import requests
from pydantic import Field, conlist, root_validator

from nonbonded.library.config import settings
from nonbonded.library.models import BaseORM, BaseREST
from nonbonded.library.models.authors import Author
from nonbonded.library.models.exceptions import MutuallyExclusiveError
from nonbonded.library.models.forcebalance import ForceBalanceOptions
from nonbonded.library.models.forcefield import ForceField, Parameter
from nonbonded.library.models.validators.string import NonEmptyStr
from nonbonded.library.utilities.environments import ChemicalEnvironment

if TYPE_CHECKING:
    PositiveFloat = float
else:
    from pydantic import PositiveFloat


class Optimization(BaseREST):

    id: NonEmptyStr = Field(
        ..., description="The unique id assigned to this optimization."
    )
    study_id: NonEmptyStr = Field(..., description="The id of the parent study.")
    project_id: NonEmptyStr = Field(..., description="The id of the parent project.")

    name: NonEmptyStr = Field(..., description="The name of the optimization.")
    description: NonEmptyStr = Field(
        ..., description="A description of this optimization."
    )

    training_set_ids: conlist(NonEmptyStr, min_items=1) = Field(
        ...,
        description="The unique identifiers of the data sets to use as part of the "
        "optimization.",
    )

    initial_force_field: ForceField = Field(
        ...,
        description="The file name of the force field which will be used as "
        "the starting point for all optimizations.",
    )

    parameters_to_train: conlist(Parameter, min_items=1) = Field(
        ..., description="The force field parameters to be optimized."
    )
    force_balance_input: ForceBalanceOptions = Field(
        default_factory=ForceBalanceOptions,
        description="The inputs to use for the optimization.",
    )

    denominators: Dict[NonEmptyStr, NonEmptyStr] = Field(
        ...,
        description="The denominators to scale each class of properties "
        "contribution to the objective function by.",
    )
    priors: Dict[NonEmptyStr, PositiveFloat] = Field(
        ..., description="The priors to place on each class of parameter."
    )

    analysis_environments: List[ChemicalEnvironment] = Field(
        ...,
        description="The chemical environments to consider when analysing the results "
        "of the optimization.",
    )

    @classmethod
    def _get_endpoint(cls, *, project_id: str, study_id: str, optimization_id: str):
        return (
            f"{settings.API_URL}/projects/"
            f"{project_id}"
            f"/studies/"
            f"{study_id}"
            f"/optimizations/"
            f"{optimization_id}"
        )

    def _post_endpoint(self):
        return (
            f"{settings.API_URL}/projects/"
            f"{self.project_id}"
            f"/studies/"
            f"{self.study_id}"
            f"/optimizations/"
        )

    def _put_endpoint(self):
        return (
            f"{settings.API_URL}/projects/"
            f"{self.project_id}"
            f"/studies/"
            f"{self.study_id}"
            f"/optimizations/"
        )

    def _delete_endpoint(self):

        return (
            f"{settings.API_URL}/projects/"
            f"{self.project_id}"
            f"/studies/"
            f"{self.study_id}"
            f"/optimizations/"
            f"{self.id}"
        )

    @classmethod
    def from_rest(
        cls,
        *,
        project_id: str,
        study_id: str,
        optimization_id: str,
        requests_class=requests,
    ) -> "Optimization":
        # noinspection PyTypeChecker
        return super(Optimization, cls).from_rest(
            project_id=project_id,
            study_id=study_id,
            optimization_id=optimization_id,
            requests_class=requests_class,
        )


class Benchmark(BaseREST):

    id: NonEmptyStr = Field(
        ..., description="The unique id assigned to this benchmark."
    )
    study_id: NonEmptyStr = Field(..., description="The id of the parent study.")
    project_id: NonEmptyStr = Field(..., description="The id of the parent project.")

    name: NonEmptyStr = Field(..., description="The name of the benchmark.")
    description: NonEmptyStr = Field(
        ..., description="A description of this benchmark."
    )

    test_set_ids: conlist(NonEmptyStr, min_items=1) = Field(
        ...,
        description="The unique identifiers of the data sets to use as part of the "
        "benchmarking.",
    )

    optimization_id: Optional[NonEmptyStr] = Field(
        ...,
        description="The id of the optimization that should be benchmarked. This must "
        "be the id of an optimization which is part of the same study and project. "
        "This option is mutually exclusive with `force_field_name`.",
    )
    force_field_name: Optional[NonEmptyStr] = Field(
        ...,
        description="The file name of the force field to use in the benchmark. This "
        "must be the name of a force field in the `openforcefields` GitHub repository. "
        "This option is mutually exclusive with `optimized_id`.",
    )

    analysis_environments: List[ChemicalEnvironment] = Field(
        ...,
        description="The chemical environments to consider when analysing the results "
        "of the benchmark.",
    )

    @root_validator
    def _validate_mutually_exclusive(cls, values):

        optimization_id = values.get("optimization_id")
        force_field_name = values.get("force_field_name")

        if (optimization_id is None and force_field_name is None) or (
            optimization_id is not None and force_field_name is not None
        ):
            raise MutuallyExclusiveError("optimization_id", "force_field_name")

        return values

    @classmethod
    def _get_endpoint(cls, *, project_id: str, study_id: str, benchmark_id: str):
        return (
            f"{settings.API_URL}/projects/"
            f"{project_id}"
            f"/studies/"
            f"{study_id}"
            f"/benchmarks/"
            f"{benchmark_id}"
        )

    def _post_endpoint(self):
        return (
            f"{settings.API_URL}/projects/"
            f"{self.project_id}"
            f"/studies/"
            f"{self.study_id}"
            f"/benchmarks/"
        )

    def _put_endpoint(self):
        return (
            f"{settings.API_URL}/projects/"
            f"{self.project_id}"
            f"/studies/"
            f"{self.study_id}"
            f"/benchmarks/"
        )

    def _delete_endpoint(self):

        return (
            f"{settings.API_URL}/projects/"
            f"{self.project_id}"
            f"/studies/"
            f"{self.study_id}"
            f"/benchmarks/"
            f"{self.id}"
        )

    @classmethod
    def from_rest(
        cls,
        *,
        project_id: str,
        study_id: str,
        benchmark_id: str,
        requests_class=requests,
    ) -> "Benchmark":
        # noinspection PyTypeChecker
        return super(Benchmark, cls).from_rest(
            project_id=project_id,
            study_id=study_id,
            benchmark_id=benchmark_id,
            requests_class=requests_class,
        )


class Study(BaseREST):

    id: NonEmptyStr = Field(..., description="The unique id assigned to this study.")
    project_id: NonEmptyStr = Field(..., description="The id of the parent project.")

    name: NonEmptyStr = Field(..., description="The name of the study.")
    description: NonEmptyStr = Field(..., description="A description of this study.")

    optimizations: List[Optimization] = Field(
        default_factory=list,
        description="The optimizations to perform as part of this study.",
    )
    benchmarks: List[Benchmark] = Field(
        default_factory=list,
        description="The benchmarks to perform as part of this study.",
    )

    @root_validator
    def _validate_studies(cls, values):

        study_id = values.get("id")

        optimizations: List[Optimization] = values.get("optimizations")
        benchmarks: List[Benchmark] = values.get("benchmarks")

        assert all(optimization.study_id == study_id for optimization in optimizations)
        assert all(benchmark.study_id == study_id for benchmark in benchmarks)

        optimization_ids = set(x.id for x in optimizations)

        assert len(optimization_ids) == len(optimizations)
        assert len(set(x.id for x in benchmarks)) == len(benchmarks)

        assert all(
            benchmark.optimization_id is None
            or benchmark.optimization_id in optimization_ids
            for benchmark in benchmarks
        )

        return values

    @classmethod
    def _get_endpoint(cls, *, project_id: str, study_id: str):
        return f"{settings.API_URL}/projects/{project_id}/studies/{study_id}"

    def _post_endpoint(self):
        return f"{settings.API_URL}/projects/{self.project_id}/studies/"

    def _put_endpoint(self):
        return f"{settings.API_URL}/projects/{self.project_id}/studies/"

    def _delete_endpoint(self):

        return (
            f"{settings.API_URL}/projects/"
            f"{self.project_id}"
            f"/studies/"
            f"{self.id}"
        )

    @classmethod
    def from_rest(
        cls, *, project_id: str, study_id: str, requests_class=requests
    ) -> "Study":

        # noinspection PyTypeChecker
        return super(Study, cls).from_rest(
            project_id=project_id, study_id=study_id, requests_class=requests_class
        )


class StudyCollection(BaseORM):

    studies: List[Study] = Field(
        default_factory=list, description="A collection of studies.",
    )

    @classmethod
    def from_rest(cls, project_id: str, requests_class=requests) -> "StudyCollection":

        studies_request = requests_class.get(
            f"{settings.API_URL}/projects/{project_id}/studies/"
        )
        try:
            studies_request.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(error.response.text)
            raise

        studies = StudyCollection.parse_raw(studies_request.text)
        return studies


class Project(BaseREST):

    id: NonEmptyStr = Field(..., description="The unique id assigned to the project.")

    name: NonEmptyStr = Field(..., description="The name of the project.")
    description: NonEmptyStr = Field(..., description="A description of the project.")
    authors: conlist(Author, min_items=1) = Field(
        ..., description="The authors of the project."
    )

    studies: List[Study] = Field(
        default_factory=list,
        description="The studies conducted as part of the project.",
    )

    @root_validator
    def _validate_studies(cls, values):

        project_id = values.get("id")
        studies = values.get("studies")

        assert len(set(x.id for x in studies)) == len(studies)

        assert all(
            (
                study.project_id == project_id
                and all(opt.project_id == project_id for opt in study.optimizations)
                and all(bench.project_id == project_id for bench in study.benchmarks)
            )
            for study in studies
        )

        return values

    @classmethod
    def _get_endpoint(cls, *, project_id: str):
        return f"{settings.API_URL}/projects/{project_id}"

    def _post_endpoint(self):
        return f"{settings.API_URL}/projects/"

    def _put_endpoint(self):
        return f"{settings.API_URL}/projects/"

    def _delete_endpoint(self):
        return f"{settings.API_URL}/projects/{self.id}"

    @classmethod
    def from_rest(cls, *, project_id: str, requests_class=requests) -> "Project":
        # noinspection PyTypeChecker
        return super(Project, cls).from_rest(
            project_id=project_id, requests_class=requests_class
        )


class ProjectCollection(BaseORM):

    projects: List[Project] = Field(
        default_factory=list, description="A collection of projects.",
    )

    @classmethod
    def from_rest(cls, requests_class=requests) -> "ProjectCollection":

        projects_request = requests_class.get(f"{settings.API_URL}/projects/")
        try:
            projects_request.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(error.response.text)
            raise

        projects = ProjectCollection.parse_raw(projects_request.text)
        return projects
