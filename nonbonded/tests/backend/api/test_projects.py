from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models.projects import (
    Benchmark,
    BenchmarkCollection,
    Optimization,
    OptimizationCollection,
    Project,
    ProjectCollection,
    Study,
    StudyCollection,
)
from nonbonded.tests.backend.api.utilities import (
    BaseTestEndpoints,
    commit_benchmark,
    commit_data_set,
    commit_optimization,
    commit_project,
    commit_study,
)
from nonbonded.tests.utilities.comparison import compare_pydantic_models
from nonbonded.tests.utilities.factory import (
    create_benchmark,
    create_evaluator_target,
    create_force_field,
    create_optimization,
    create_project,
    create_study,
)


class TestProjectEndpoints(BaseTestEndpoints):
    @classmethod
    def _rest_class(cls):
        return Project

    @classmethod
    def _create_model(cls, db, create_dependencies=True):
        project = create_project("project-1")
        return project, {"project_id": project.id}

    @classmethod
    def _perturb_model(cls, model):
        model.name = "Updated"

    @classmethod
    def _commit_model(cls, db):
        project = commit_project(db)
        return project, {"project_id": project.id}

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.Project.id).count()

    def test_get_all(self, rest_client: TestClient, db: Session):

        project = commit_project(db)
        rest_collection = ProjectCollection.from_rest(requests_class=rest_client)

        assert rest_collection is not None
        assert len(rest_collection.projects) == 1

        compare_pydantic_models(project, rest_collection.projects[0])


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

        study = create_study(project_id, "study-1")

        return study, {"project_id": project_id, "study_id": study.id}

    @classmethod
    def _perturb_model(cls, model):
        model.name = "Updated"

    @classmethod
    def _commit_model(cls, db):
        project, study = commit_study(db)
        return study, {"project_id": project.id, "study_id": study.id}

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.Study.id).count()

    def test_get_all(self, rest_client: TestClient, db: Session):

        project, study = commit_study(db)
        rest_collection = StudyCollection.from_rest(
            project_id=project.id, requests_class=rest_client
        )

        assert rest_collection is not None
        assert len(rest_collection.studies) == 1

        compare_pydantic_models(study, rest_collection.studies[0])


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
                "sub_study_id": benchmark.id,
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
                "sub_study_id": benchmark.id,
            },
        )

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.Benchmark.id).count()

    def test_get_all(self, rest_client: TestClient, db: Session):

        project, study, benchmark, _, _, _ = commit_benchmark(db, False)
        rest_collection = BenchmarkCollection.from_rest(
            project_id=project.id, study_id=study.id, requests_class=rest_client
        )

        assert rest_collection is not None
        assert len(rest_collection.benchmarks) == 1

        compare_pydantic_models(benchmark, rest_collection.benchmarks[0])


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
            [create_evaluator_target("name", data_set_ids)],
        )

        return (
            optimization,
            {
                "project_id": project_id,
                "study_id": study_id,
                "sub_study_id": optimization.id,
            },
        )

    @classmethod
    def _perturb_model(cls, model):
        model.name = "Updated"

    @classmethod
    def _commit_model(cls, db):
        project, study, optimization, _, _ = commit_optimization(db)

        return (
            optimization,
            {
                "project_id": project.id,
                "study_id": study.id,
                "sub_study_id": optimization.id,
            },
        )

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.Optimization.id).count()

    def test_get_all(self, rest_client: TestClient, db: Session):

        project, study, optimization, _, _ = commit_optimization(db)
        rest_collection = OptimizationCollection.from_rest(
            project_id=project.id, study_id=study.id, requests_class=rest_client
        )

        assert rest_collection is not None
        assert len(rest_collection.optimizations) == 1

        compare_pydantic_models(optimization, rest_collection.optimizations[0])
