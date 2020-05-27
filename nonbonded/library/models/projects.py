"""A collection of models which outline the scope and options of a particular project.
"""
from typing import Dict, List, Optional

from pydantic import Field, root_validator, validator

from nonbonded.library.config import settings
from nonbonded.library.models import BaseORM, BaseREST
from nonbonded.library.models.authors import Author
from nonbonded.library.models.forcebalance import ForceBalanceOptions
from nonbonded.library.models.forcefield import ForceField, Parameter
from nonbonded.library.models.validators.collection import not_empty
from nonbonded.library.utilities.environments import ChemicalEnvironment


class Optimization(BaseREST):

    id: str = Field(..., description="The unique id assigned to this optimization.")
    study_id: str = Field(..., description="The id of the parent study.")
    project_id: Optional[str] = Field(..., description="The id of the parent project.")

    name: str = Field(..., description="The name of the optimization.")
    description: str = Field(..., description="A description of this optimization.")

    training_set_ids: List[str] = Field(
        ...,
        description="The unique identifiers of the data sets to use as part of the "
        "optimization.",
    )

    initial_force_field: ForceField = Field(
        ...,
        description="The file name of the force field which will be used as "
        "the starting point for all optimizations.",
    )

    parameters_to_train: List[Parameter] = Field(
        ..., description="The force field parameters to be optimized."
    )
    force_balance_input: ForceBalanceOptions = Field(
        default_factory=ForceBalanceOptions,
        description="The inputs to use for the optimization.",
    )

    denominators: Dict[str, str] = Field(
        ...,
        description="The denominators to scale each class of properties "
        "contribution to the objective function by.",
    )
    priors: Dict[str, float] = Field(
        ..., description="The priors to place on each class of parameter."
    )

    analysis_environments: List[ChemicalEnvironment] = Field(
        ...,
        description="The chemical environments to consider when analysing the results "
        "of the optimization.",
    )

    _validate_training_set_ids = validator("training_set_ids", allow_reuse=True)(
        not_empty
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
    def from_rest(cls, project_id: str, study_id: str, optimization_id: str):

        import requests

        request = requests.get(
            f"{settings.API_URL}/projects/"
            f"{project_id}"
            f"/studies/"
            f"{study_id}"
            f"/optimizations/"
            f"{optimization_id}"
        )

        return cls._from_rest(request)


class OptimizationCollection(BaseORM):

    optimizations: List[Optimization] = Field(
        default_factory=list, description="A collection of optimizations.",
    )

    @classmethod
    def from_rest(cls, project_id: str, study_id: str) -> "OptimizationCollection":

        import requests

        optimizations_request = requests.get(
            f"{settings.API_URL}/projects/"
            f"{project_id}"
            f"/studies/"
            f"{study_id}"
            f"/optimizations/"
        )
        optimizations_request.raise_for_status()

        optimizations = OptimizationCollection.parse_raw(optimizations_request.text)
        return optimizations


class Benchmark(BaseREST):

    id: str = Field(..., description="The unique id assigned to this benchmark.")
    study_id: str = Field(..., description="The id of the parent study.")
    project_id: str = Field(..., description="The id of the parent project.")

    name: str = Field(..., description="The name of the benchmark.")
    description: str = Field(..., description="A description of this benchmark.")

    test_set_ids: List[str] = Field(
        ...,
        description="The unique identifiers of the data sets to use as part of the "
        "benchmarking.",
    )

    optimization_id: Optional[str] = Field(
        ...,
        description="The id of the optimization that should be benchmarked. This must "
        "be the id of an optimization which is part of the same study and project. "
        "This option is mutually exclusive with `force_field_name`.",
    )
    force_field_name: Optional[str] = Field(
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

    _validate_test_set_ids = validator("test_set_ids", allow_reuse=True)(not_empty)

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
    def from_rest(cls, project_id: str, study_id: str, benchmark_id: str):

        import requests

        request = requests.get(
            f"{settings.API_URL}/projects/"
            f"{project_id}"
            f"/studies/"
            f"{study_id}"
            f"/benchmarks/"
            f"{benchmark_id}"
        )

        return cls._from_rest(request)


class BenchmarkCollection(BaseORM):

    benchmarks: List[Benchmark] = Field(
        default_factory=list, description="A collection of benchmarks.",
    )

    @classmethod
    def from_rest(cls, project_id: str, study_id: str) -> "BenchmarkCollection":

        import requests

        benchmarks_request = requests.get(
            f"{settings.API_URL}/projects/"
            f"{project_id}"
            f"/studies/"
            f"{study_id}"
            f"/benchmarks/"
        )
        benchmarks_request.raise_for_status()

        benchmarks = BenchmarkCollection.parse_raw(benchmarks_request.text)
        return benchmarks


class Study(BaseREST):

    id: str = Field(..., description="The unique id assigned to this study.")
    project_id: str = Field(..., description="The id of the parent project.")

    name: str = Field(..., description="The name of the study.")
    description: str = Field(..., description="A description of this study.")

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

        optimizations = values.get("optimizations")
        benchmarks = values.get("benchmarks")

        assert all(optimization.study_id == study_id for optimization in optimizations)
        assert all(benchmark.study_id == study_id for benchmark in benchmarks)

        assert len(set(x.id for x in optimizations)) == len(optimizations)
        assert len(set(x.id for x in benchmarks)) == len(benchmarks)

        return values

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
    def from_rest(cls, project_id: str, study_id: str):

        import requests

        request = requests.get(
            f"{settings.API_URL}/projects/{project_id}/studies/{study_id}"
        )

        return cls._from_rest(request)


class StudyCollection(BaseORM):

    studies: List[Study] = Field(
        default_factory=list, description="A collection of studies.",
    )

    @classmethod
    def from_rest(cls, project_id: str) -> "StudyCollection":

        import requests

        studies_request = requests.get(
            f"{settings.API_URL}/projects/{project_id}/studies/"
        )
        studies_request.raise_for_status()

        studies = StudyCollection.parse_raw(studies_request.text)
        return studies


class Project(BaseREST):

    id: str = Field(..., description="The unique id assigned to the project.")

    name: str = Field(..., description="The name of the project.")
    description: str = Field(..., description="A description of the project.")
    authors: List[Author] = Field(..., description="The authors of the project.")

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

    _validate_authors = validator("authors", allow_reuse=True)(not_empty)

    def _post_endpoint(self):
        return f"{settings.API_URL}/projects/"

    def _put_endpoint(self):
        return f"{settings.API_URL}/projects/"

    def _delete_endpoint(self):
        return f"{settings.API_URL}/projects/{self.id}"

    @classmethod
    def from_rest(cls, project_id: str):
        import requests

        request = requests.get(f"{settings.API_URL}/projects/{project_id}")
        return cls._from_rest(request)


class ProjectCollection(BaseORM):

    projects: List[Project] = Field(
        default_factory=list, description="A collection of projects.",
    )

    @classmethod
    def from_rest(cls) -> "ProjectCollection":
        import requests

        projects_request = requests.get("{settings.API_URL}/projects/")
        projects_request.raise_for_status()

        projects = ProjectCollection.parse_raw(projects_request.text)
        return projects
