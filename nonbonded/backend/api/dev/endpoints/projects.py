from fastapi import APIRouter, Depends
from fastapi.openapi.models import APIKey
from sqlalchemy.orm import Session

from nonbonded.backend.api import depends
from nonbonded.backend.api.base import BaseCRUDEndpoint
from nonbonded.backend.core.security import check_access_token
from nonbonded.backend.database import models
from nonbonded.backend.database.crud.projects import (
    BenchmarkCRUD,
    OptimizationCRUD,
    ProjectCRUD,
    StudyCRUD,
)
from nonbonded.backend.database.crud.results import (
    BenchmarkResultCRUD,
    OptimizationResultCRUD,
)
from nonbonded.library.models.projects import (
    Benchmark,
    Optimization,
    Project,
    ProjectCollection,
    Study,
    StudyCollection,
)
from nonbonded.library.models.results import BenchmarkResult, OptimizationResult

router = APIRouter()


class ProjectEndpoints(BaseCRUDEndpoint):
    @classmethod
    def _crud_class(cls):
        return ProjectCRUD

    @staticmethod
    @router.get("/", response_model=ProjectCollection)
    async def get_all(
        skip: int = 0, limit: int = 100, db: Session = Depends(depends.get_db)
    ):
        db_projects = ProjectCRUD.read_all(db, skip=skip, limit=limit)
        return ProjectCollection(projects=db_projects)

    @staticmethod
    @router.get("/{project_id}", response_model=Project)
    async def get(project_id, db: Session = Depends(depends.get_db)):
        return ProjectEndpoints._read_function(db, project_id=project_id)

    @staticmethod
    @router.post("/")
    async def post(
        project: Project,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return ProjectEndpoints._post(db, project)

    @staticmethod
    @router.put("/")
    async def put(
        project: Project,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return ProjectEndpoints._put(db, project)

    @staticmethod
    @router.delete("/{project_id}")
    async def delete(
        project_id,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        ProjectEndpoints._delete(db, project_id=project_id)


class StudyEndpoints(BaseCRUDEndpoint):
    @classmethod
    def _crud_class(cls):
        return StudyCRUD

    @staticmethod
    @router.get("/{project_id}/studies/", response_model=StudyCollection)
    async def get_all(project_id, db: Session = Depends(depends.get_db)):
        return {"studies": StudyCRUD.read_all(db, project_id)}

    @staticmethod
    @router.get("/{project_id}/studies/{study_id}", response_model=Study)
    async def get(project_id, study_id, db: Session = Depends(depends.get_db)):
        return StudyEndpoints._read_function(
            db, project_id=project_id, study_id=study_id
        )

    @staticmethod
    @router.post("/{project_id}/studies/")
    async def post(
        study: Study,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return StudyEndpoints._post(db, study)

    @staticmethod
    @router.put("/{project_id}/studies/")
    async def put(
        study: Study,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return StudyEndpoints._put(db, study)

    @staticmethod
    @router.delete("/{project_id}/studies/{study_id}")
    async def delete(
        project_id,
        study_id,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return StudyEndpoints._delete(db, project_id=project_id, study_id=study_id)


class OptimizationEndpoints(BaseCRUDEndpoint):
    @classmethod
    def _crud_class(cls):
        return OptimizationCRUD

    @staticmethod
    @router.get("/{project_id}/studies/{study_id}/optimizations/{optimization_id}")
    async def get(
        project_id,
        study_id,
        optimization_id,
        db: Session = Depends(depends.get_db),
    ):
        return OptimizationEndpoints._read_function(
            db,
            project_id=project_id,
            study_id=study_id,
            sub_study_id=optimization_id,
        )

    @staticmethod
    @router.post("/{project_id}/studies/{study_id}/optimizations/")
    async def post_optimization(
        optimization: Optimization,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return OptimizationEndpoints._post(db, optimization)

    @staticmethod
    @router.put("/{project_id}/studies/{study_id}/optimizations/")
    async def put_optimization(
        optimization: Optimization,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return OptimizationEndpoints._put(db, optimization)

    @staticmethod
    @router.delete("/{project_id}/studies/{study_id}/optimizations/{optimization_id}")
    async def delete_optimization(
        project_id,
        study_id,
        optimization_id,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return OptimizationEndpoints._delete(
            db,
            project_id=project_id,
            study_id=study_id,
            sub_study_id=optimization_id,
        )


class OptimizationResultEndpoints(BaseCRUDEndpoint):
    @classmethod
    def _crud_class(cls):
        return OptimizationResultCRUD

    @staticmethod
    @router.get(
        "/{project_id}/studies/{study_id}/optimizations/{optimization_id}/results/"
    )
    async def get_optimization_result(
        project_id,
        study_id,
        optimization_id,
        db: Session = Depends(depends.get_db),
    ):

        db_optimization_result = OptimizationResultCRUD.read(
            db,
            project_id=project_id,
            study_id=study_id,
            sub_study_id=optimization_id,
        )

        return db_optimization_result

    @staticmethod
    @router.post(
        "/{project_id}/studies/{study_id}/optimizations/{optimization_id}/results/"
    )
    async def post_optimization_result_result(
        optimization_result: OptimizationResult,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return OptimizationResultEndpoints._post(db, optimization_result)

    @staticmethod
    @router.delete(
        "/{project_id}/studies/{study_id}/optimizations/{optimization_id}/results/"
    )
    async def delete_optimization_result(
        project_id,
        study_id,
        optimization_id,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        OptimizationResultEndpoints._delete(
            db,
            project_id=project_id,
            study_id=study_id,
            sub_study_id=optimization_id,
        )


class BenchmarkEndpoints(BaseCRUDEndpoint):
    @classmethod
    def _crud_class(cls):
        return BenchmarkCRUD

    @staticmethod
    @router.get("/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}")
    async def get(
        project_id,
        study_id,
        benchmark_id,
        db: Session = Depends(depends.get_db),
    ):
        return BenchmarkEndpoints._read_function(
            db, project_id=project_id, study_id=study_id, sub_study_id=benchmark_id
        )

    @staticmethod
    @router.post("/{project_id}/studies/{study_id}/benchmarks/")
    async def post_benchmark(
        benchmark: Benchmark,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return BenchmarkEndpoints._post(db, benchmark)

    @staticmethod
    @router.put("/{project_id}/studies/{study_id}/benchmarks/")
    async def put_benchmark(
        benchmark: Benchmark,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return BenchmarkEndpoints._put(db, benchmark)

    @staticmethod
    @router.delete("/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}")
    async def delete_benchmark(
        project_id,
        study_id,
        benchmark_id,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return BenchmarkEndpoints._delete(
            db, project_id=project_id, study_id=study_id, sub_study_id=benchmark_id
        )


class BenchmarkResultEndpoints(BaseCRUDEndpoint):
    @classmethod
    def _crud_class(cls):
        return BenchmarkResultCRUD

    @classmethod
    def _db_to_model(cls, db_model: models.BenchmarkResult) -> BenchmarkResult:
        return cls._crud_class().db_to_model(db_model)

    @staticmethod
    @router.get("/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}/results/")
    async def get(
        project_id,
        study_id,
        benchmark_id,
        db: Session = Depends(depends.get_db),
    ):

        db_benchmark_result = BenchmarkResultCRUD.read(
            db,
            project_id=project_id,
            study_id=study_id,
            sub_study_id=benchmark_id,
        )

        return db_benchmark_result

    @staticmethod
    @router.post("/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}/results/")
    async def post(
        benchmark_result: BenchmarkResult,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return BenchmarkResultEndpoints._post(db, benchmark_result)

    @staticmethod
    @router.delete(
        "/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}/results/"
    )
    async def delete(
        project_id,
        study_id,
        benchmark_id,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        BenchmarkResultEndpoints._delete(
            db, project_id=project_id, study_id=study_id, sub_study_id=benchmark_id
        )
