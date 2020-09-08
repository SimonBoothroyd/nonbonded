"""A collection of models which outline the scope and options of a particular project.
"""
import abc
from typing import TYPE_CHECKING, List, Optional, Union

import requests
from pydantic import Field, conlist, root_validator, validator

from nonbonded.library.config import settings
from nonbonded.library.models import BaseORM, BaseREST
from nonbonded.library.models.authors import Author
from nonbonded.library.models.engines import ForceBalance
from nonbonded.library.models.exceptions import MutuallyExclusiveError
from nonbonded.library.models.exceptions.exceptions import DuplicateItemsError
from nonbonded.library.models.forcefield import ForceField, Parameter
from nonbonded.library.models.targets import OptimizationTarget
from nonbonded.library.models.validators.string import IdentifierStr, NonEmptyStr
from nonbonded.library.utilities.environments import ChemicalEnvironment

if TYPE_CHECKING:
    PositiveInt = int
else:
    from pydantic import PositiveInt


class SubStudy(BaseREST, abc.ABC):
    """A base class for optimization and benchmark sub-studies, which share largely the
    same fields.
    """

    id: IdentifierStr = Field(
        ..., description="The unique id assigned to this sub-study."
    )

    study_id: IdentifierStr = Field(..., description="The id of the parent study.")
    project_id: IdentifierStr = Field(..., description="The id of the parent project.")

    name: NonEmptyStr = Field(..., description="The name of the sub-study.")
    description: NonEmptyStr = Field(
        ..., description="A description of this sub-study."
    )

    force_field: Optional[ForceField] = Field(
        None,
        description="The force field which will be used in this sub-study. If this is "
        "a force field produced by an optimization from the parent study, the "
        "``optimization_id`` input should be used instead. This option is mutually "
        "exclusive with `optimization_id`.",
    )
    optimization_id: Optional[IdentifierStr] = Field(
        None,
        description="The id of the optimization which produced the force field to use "
        "in this sub-study. This must be the id of an optimization which is part of "
        "the same study and project. This option is mutually exclusive with "
        "``force_field``.",
    )

    analysis_environments: List[ChemicalEnvironment] = Field(
        ...,
        description="The chemical environments to consider when analysing the results "
        "of this sub-study.",
    )

    @root_validator
    def _validate_mutually_exclusive(cls, values):

        optimization_id = values.get("optimization_id")
        force_field = values.get("force_field")

        if (optimization_id is None and force_field is None) or (
            optimization_id is not None and force_field is not None
        ):
            raise MutuallyExclusiveError("optimization_id", "force_field")

        return values


class SubStudyCollection(BaseORM, abc.ABC):
    @classmethod
    @abc.abstractmethod
    def sub_study_type(cls):
        """The type of sub-study stored in this collection."""

    @classmethod
    def from_rest(cls, project_id: str, study_id: str, requests_class=requests):

        sub_studies_request = requests_class.get(
            f"{settings.API_URL}/projects/"
            f"{project_id}"
            f"/studies/"
            f"{study_id}"
            f"/f{cls.sub_study_type.__name__.lower()}s/"
        )
        try:
            sub_studies_request.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(error.response.text)
            raise

        sub_studies = cls.parse_raw(sub_studies_request.text)
        return sub_studies


class Optimization(SubStudy):

    engine: Union[ForceBalance] = Field(
        ...,
        description="The engine to use to drive the optimization.",
    )
    targets: conlist(OptimizationTarget, min_items=1) = Field(
        ...,
        description="A list of the fitting targets to include in the optimization. "
        "These represent different kinds of contributions to the objective function, "
        "such as deviations from experimental measurements or from computed QM data.",
    )

    max_iterations: PositiveInt = Field(
        ...,
        description="The maximum number of optimization iterations to perform. The "
        "number actually performed may be less depending on if the optimization engine "
        "supports automatically detecting whether the optimization has converged.",
    )

    parameters_to_train: conlist(Parameter, min_items=1) = Field(
        ..., description="The force field parameters to be optimized."
    )

    @validator("parameters_to_train")
    def _validate_unique_parameters(cls, value: List[Parameter]) -> List[Parameter]:

        unique_parameters = set()
        duplicate_parameters = set()

        for parameter in value:

            if parameter in unique_parameters:
                duplicate_parameters.add(parameter)

            unique_parameters.add(parameter)

        if len(duplicate_parameters) > 0:
            raise DuplicateItemsError("parameters_to_train", duplicate_parameters)

        return value

    @validator("targets")
    def _validate_unique_target_names(
        cls, value: List[OptimizationTarget]
    ) -> List[OptimizationTarget]:

        names = {target.id for target in value}
        assert len(names) == len(value)

        return value

    @classmethod
    def _get_endpoint(cls, *, project_id: str, study_id: str, sub_study_id: str):
        return (
            f"{settings.API_URL}/projects/"
            f"{project_id}"
            f"/studies/"
            f"{study_id}"
            f"/optimizations/"
            f"{sub_study_id}"
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

    @root_validator
    def _validate_self_reference(cls, values):

        identifier = values.get("id")
        optimization_id = values.get("optimization_id")

        assert optimization_id is None or optimization_id != identifier

        return values

    @classmethod
    def from_rest(
        cls,
        *,
        project_id: str,
        study_id: str,
        sub_study_id: str,
        requests_class=requests,
    ) -> "Optimization":
        # noinspection PyTypeChecker
        return super(Optimization, cls).from_rest(
            project_id=project_id,
            study_id=study_id,
            sub_study_id=sub_study_id,
            requests_class=requests_class,
        )


class OptimizationCollection(SubStudyCollection):
    @classmethod
    def sub_study_type(cls):
        return Optimization

    optimizations: List[Optimization] = Field(
        default_factory=list,
        description="A collection of optimizations.",
    )


class Benchmark(SubStudy):

    test_set_ids: conlist(IdentifierStr, min_items=1) = Field(
        ...,
        description="The unique identifiers of the data sets to use as part of the "
        "benchmarking.",
    )

    @classmethod
    def _get_endpoint(cls, *, project_id: str, study_id: str, sub_study_id: str):
        return (
            f"{settings.API_URL}/projects/"
            f"{project_id}"
            f"/studies/"
            f"{study_id}"
            f"/benchmarks/"
            f"{sub_study_id}"
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
        sub_study_id: str,
        requests_class=requests,
    ) -> "Benchmark":
        # noinspection PyTypeChecker
        return super(Benchmark, cls).from_rest(
            project_id=project_id,
            study_id=study_id,
            sub_study_id=sub_study_id,
            requests_class=requests_class,
        )


class BenchmarkCollection(SubStudyCollection):
    @classmethod
    def sub_study_type(cls):
        return Benchmark

    benchmarks: List[Benchmark] = Field(
        default_factory=list,
        description="A collection of benchmarks.",
    )


class Study(BaseREST):

    id: IdentifierStr = Field(..., description="The unique id assigned to this study.")
    project_id: IdentifierStr = Field(..., description="The id of the parent project.")

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
        default_factory=list,
        description="A collection of studies.",
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

    id: IdentifierStr = Field(..., description="The unique id assigned to the project.")

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
        default_factory=list,
        description="A collection of projects.",
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
