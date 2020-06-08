from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.config import settings
from nonbonded.library.models.datasets import DataSetCollection
from nonbonded.library.models.projects import (
    Benchmark,
    Optimization,
    Project,
    ProjectCollection,
    Study,
    StudyCollection,
)
from nonbonded.tests.backend.api.utilities import BaseTestEndpoints
from nonbonded.tests.backend.crud.utilities.commit import (
    commit_benchmark,
    commit_data_set,
    commit_optimization,
    commit_project,
    commit_study,
)
from nonbonded.tests.backend.crud.utilities.comparison import (
    compare_benchmarks,
    compare_optimizations,
    compare_projects,
    compare_studies,
)
from nonbonded.tests.backend.crud.utilities.create import (
    create_benchmark,
    create_empty_project,
    create_empty_study,
    create_force_field,
    create_optimization,
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

    def test_get_all(self, rest_client: TestClient, rest_db: Session):

        project = commit_project(rest_db)
        rest_collection = ProjectCollection.from_rest(rest_client)

        assert rest_collection is not None
        assert len(rest_collection.projects) == 1

        compare_projects(project, rest_collection.projects[0])


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

    def test_get_all(self, rest_client: TestClient, rest_db: Session):

        project, study = commit_study(rest_db)
        rest_collection = StudyCollection.from_rest(
            project_id=project.id, requests_class=rest_client
        )

        assert rest_collection is not None
        assert len(rest_collection.studies) == 1

        compare_studies(study, rest_collection.studies[0])

    def test_get_all_data_sets(self, rest_client: TestClient, rest_db: Session):

        project, study, optimization, data_set = commit_optimization(rest_db)

        data_sets_request = rest_client.get(
            f"{settings.API_URL}/projects/{project.id}/studies/{study.id}/datasets"
        )
        data_sets_request.raise_for_status()

        rest_data_sets = DataSetCollection.parse_raw(data_sets_request.text)

        assert rest_data_sets is not None
        assert len(rest_data_sets.data_sets) == 2


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
            create_force_field(),
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
            project_id, study_id, "optimization-1", data_set_ids,
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
