from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models.projects import Benchmark, Project, Study, Optimization
from nonbonded.library.models.results import OptimizationResult
from nonbonded.tests.backend.api.utilities import BaseTestEndpoints
from nonbonded.tests.backend.crud.utilities.commit import (
    commit_benchmark,
    commit_data_set,
    commit_project,
    commit_study, commit_optimization,
)
from nonbonded.tests.backend.crud.utilities.comparison import (
    compare_benchmarks,
    compare_projects,
    compare_studies, compare_optimizations,
)
from nonbonded.tests.backend.crud.utilities.create import (
    create_benchmark,
    create_empty_project,
    create_empty_study, create_optimization,
)


class TestProjectEndpoints(BaseTestEndpoints):
    @classmethod
    def _rest_class(cls):
        return Project

    @classmethod
    def _create_model(cls, db, create_dependencies=True):
        project = create_empty_project("project-1")
        return project, {"project_id": project.id}

    @classmethod
    def _perturb_model(cls, model):
        model.name = "Updated"

    @classmethod
    def _commit_model(cls, db):
        project = commit_project(db)
        return project, {"project_id": project.id}

    @classmethod
    def _comparison_function(cls):
        return compare_projects

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.Project.id).count()


class TestStudyEndpoints(BaseTestEndpoints):
    @classmethod
    def _rest_class(cls):
        return Study

    @classmethod
    def _create_model(cls, db, create_dependencies=True):

        project_id = "project-1"

        if create_dependencies:
            project = commit_project(db)
            project_id = project.id

        study = create_empty_study(project_id, "study-1")

        return study, {"project_id": project_id, "study_id": study.id}

    @classmethod
    def _perturb_model(cls, model):
        model.name = "Updated"

    @classmethod
    def _commit_model(cls, db):
        project, study = commit_study(db)
        return study, {"project_id": project.id, "study_id": study.id}

    @classmethod
    def _comparison_function(cls):
        return compare_studies

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.Study.id).count()


class TestBenchmarkEndpoints(BaseTestEndpoints):
    @classmethod
    def _rest_class(cls):
        return Benchmark

    @classmethod
    def _create_model(cls, db, create_dependencies=True):

        project_id = "project-1"
        study_id = "study-1"

        data_set_ids = ["data-set-1"]

        if create_dependencies:

            project, study = commit_study(db)

            project_id = project.id
            study_id = study.id

            data_set = commit_data_set(db)
            data_set_ids = [data_set.id]

        benchmark = create_benchmark(
            project_id,
            study_id,
            "benchmark-1",
            data_set_ids,
            None,
            "openff-1.0.0.offxml",
        )

        return (
            benchmark,
            {
                "project_id": project_id,
                "study_id": study_id,
                "benchmark_id": benchmark.id,
            },
        )

    @classmethod
    def _perturb_model(cls, model):
        model.name = "Updated"

    @classmethod
    def _commit_model(cls, db):
        project, study, benchmark, _, _, _ = commit_benchmark(db, False)
        return (
            benchmark,
            {
                "project_id": project.id,
                "study_id": study.id,
                "benchmark_id": benchmark.id,
            },
        )

    @classmethod
    def _comparison_function(cls):
        return compare_benchmarks

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.Benchmark.id).count()


class TestOptimizationEndpoints(BaseTestEndpoints):
    @classmethod
    def _rest_class(cls):
        return Optimization

    @classmethod
    def _create_model(cls, db, create_dependencies=True):

        project_id = "project-1"
        study_id = "study-1"

        data_set_ids = ["data-set-1"]

        if create_dependencies:

            project, study = commit_study(db)

            project_id = project.id
            study_id = study.id

            data_set = commit_data_set(db)
            data_set_ids = [data_set.id]

        optimization = create_optimization(
            project_id,
            study_id,
            "optimization-1",
            data_set_ids,
        )

        return (
            optimization,
            {
                "project_id": project_id,
                "study_id": study_id,
                "optimization_id": optimization.id,
            },
        )

    @classmethod
    def _perturb_model(cls, model):
        model.name = "Updated"

    @classmethod
    def _commit_model(cls, db):
        project, study, optimization, _ = commit_optimization(db)

        return (
            optimization,
            {
                "project_id": project.id,
                "study_id": study.id,
                "optimization_id": optimization.id,
            },
        )

    @classmethod
    def _comparison_function(cls):
        return compare_optimizations

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.Optimization.id).count()
