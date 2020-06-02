from fastapi import APIRouter, Depends
from fastapi.openapi.models import APIKey
from sqlalchemy.orm import Session

from nonbonded.backend.api import depends
from nonbonded.backend.core.security import check_access_token
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
from nonbonded.library.models.datasets import DataSetCollection
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
from nonbonded.library.models.results import BenchmarkResult, OptimizationResult

router = APIRouter()


@router.get("/", response_model=ProjectCollection)
async def get_projects(
    skip: int = 0, limit: int = 100, db: Session = Depends(depends.get_db)
):

    db_projects = ProjectCRUD.read_all(db, skip=skip, limit=limit)
    return {"projects": db_projects}


@router.post("/")
async def post_project(
    project: Project,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        db_project = ProjectCRUD.create(db=db, project=project)

        db.add(db_project)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return ProjectCRUD.db_to_model(db_project)


@router.put("/")
async def put_project(
    project: Project,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        db_project = ProjectCRUD.update(db=db, project=project)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return ProjectCRUD.db_to_model(db_project)


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id, db: Session = Depends(depends.get_db)):

    db_project = ProjectCRUD.read(db, project_id)
    return db_project


@router.delete("/{project_id}")
async def delete_project(
    project_id,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        ProjectCRUD.delete(db, project_id)
        db.commit()

    except Exception as e:

        db.rollback()
        raise e


@router.get("/{project_id}/studies/", response_model=StudyCollection)
async def get_studies(project_id, db: Session = Depends(depends.get_db)):

    db_studies = StudyCRUD.read_all(db, project_id=project_id)
    return {"studies": db_studies}


@router.post("/{project_id}/studies/")
async def post_study(
    study: Study,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        db_study = StudyCRUD.create(db=db, study=study)

        db.add(db_study)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return StudyCRUD.db_to_model(db_study)


@router.put("/{project_id}/studies/")
async def put_study(
    study: Study,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        db_study = StudyCRUD.update(db=db, study=study)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return StudyCRUD.db_to_model(db_study)


@router.get("/{project_id}/studies/{study_id}", response_model=Study)
async def get_study(project_id, study_id, db: Session = Depends(depends.get_db)):

    db_study = StudyCRUD.read(db, study_id=study_id, project_id=project_id)

    return db_study


@router.get(
    "/{project_id}/studies/{study_id}/datasets/", response_model=DataSetCollection
)
async def get_study_data_sets(
    project_id, study_id, db: Session = Depends(depends.get_db)
):

    db_data_sets = StudyCRUD.read_all_data_sets(
        db, study_id=study_id, project_id=project_id
    )

    return db_data_sets


@router.delete("/{project_id}/studies/{study_id}")
async def delete_study(
    project_id,
    study_id,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        StudyCRUD.delete(db, project_id, study_id)
        db.commit()

    except Exception as e:

        db.rollback()
        raise e


@router.get(
    "/{project_id}/studies/{study_id}/optimizations/",
    response_model=OptimizationCollection,
)
async def get_optimizations(
    project_id, study_id, db: Session = Depends(depends.get_db)
):

    db_optimizations = OptimizationCRUD.read_all(
        db, project_id=project_id, study_id=study_id
    )

    return {"optimizations": db_optimizations}


@router.post("/{project_id}/studies/{study_id}/optimizations/")
async def post_optimization(
    optimization: Optimization,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        db_optimization = OptimizationCRUD.create(db=db, optimization=optimization)

        db.add(db_optimization)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return OptimizationCRUD.db_to_model(db_optimization)


@router.put("/{project_id}/studies/{study_id}/optimizations/")
async def put_optimization(
    optimization: Optimization,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        db_optimization = OptimizationCRUD.update(db=db, optimization=optimization)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return OptimizationCRUD.db_to_model(db_optimization)


@router.get("/{project_id}/studies/{study_id}/optimizations/{optimization_id}")
async def get_optimization(
    project_id, study_id, optimization_id, db: Session = Depends(depends.get_db)
):

    db_optimization = OptimizationCRUD.read(
        db, project_id=project_id, study_id=study_id, optimization_id=optimization_id
    )

    return db_optimization


@router.delete("/{project_id}/studies/{study_id}/optimizations/{optimization_id}")
async def delete_optimization(
    project_id,
    study_id,
    optimization_id,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        OptimizationCRUD.delete(db, project_id, study_id, optimization_id)
        db.commit()

    except Exception as e:

        db.rollback()
        raise e


@router.get(
    "/{project_id}/studies/{study_id}/benchmarks/", response_model=BenchmarkCollection
)
async def get_benchmarks(project_id, study_id, db: Session = Depends(depends.get_db)):

    db_benchmarks = BenchmarkCRUD.read_all(db, project_id=project_id, study_id=study_id)
    return {"benchmarks": db_benchmarks}


@router.post("/{project_id}/studies/{study_id}/benchmarks/")
async def post_benchmark(
    benchmark: Benchmark,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        db_benchmark = BenchmarkCRUD.create(db=db, benchmark=benchmark)

        db.add(db_benchmark)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return BenchmarkCRUD.db_to_model(db_benchmark)


@router.put("/{project_id}/studies/{study_id}/benchmarks/")
async def put_benchmark(
    benchmark: Benchmark,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        db_benchmark = BenchmarkCRUD.update(db=db, benchmark=benchmark)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return BenchmarkCRUD.db_to_model(db_benchmark)


@router.get("/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}",)
async def get_benchmark(
    project_id, study_id, benchmark_id, db: Session = Depends(depends.get_db)
):

    db_benchmark = BenchmarkCRUD.read(
        db, project_id=project_id, study_id=study_id, benchmark_id=benchmark_id
    )

    return db_benchmark


@router.delete("/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}")
async def delete_benchmark(
    project_id,
    study_id,
    benchmark_id,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        BenchmarkCRUD.delete(db, project_id, study_id, benchmark_id)
        db.commit()

    except Exception as e:

        db.rollback()
        raise e


@router.post(
    "/{project_id}/studies/{study_id}/optimizations/{optimization_id}/results/"
)
async def post_optimization_result_result(
    optimization_result: OptimizationResult,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        db_optimization_result = OptimizationResultCRUD.create(
            db=db, optimization_result=optimization_result
        )

        db.add(db_optimization_result)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return OptimizationResultCRUD.db_to_model(db_optimization_result)


@router.get("/{project_id}/studies/{study_id}/optimizations/{optimization_id}/results/")
async def get_optimization_result(
    project_id, study_id, optimization_id, db: Session = Depends(depends.get_db)
):

    db_optimization_result = OptimizationResultCRUD.read(
        db, project_id=project_id, study_id=study_id, optimization_id=optimization_id
    )

    return db_optimization_result


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

    try:
        OptimizationResultCRUD.delete(db, project_id, study_id, optimization_id)
        db.commit()

    except Exception as e:

        db.rollback()
        raise e


@router.post("/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}/results/")
async def post_benchmark_result(
    benchmark_result: BenchmarkResult,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        db_benchmark_result = BenchmarkResultCRUD.create(
            db=db, benchmark_result=benchmark_result
        )

        db.add(db_benchmark_result)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    # noinspection PyTypeChecker
    return BenchmarkResultCRUD.db_to_model(
        db_benchmark_result,
        db_benchmark_result.results_entries,
        db_benchmark_result.statistic_entries,
    )


@router.get("/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}/results/")
async def get_benchmark_result(
    project_id, study_id, benchmark_id, db: Session = Depends(depends.get_db)
):

    db_benchmark_result = BenchmarkResultCRUD.read(
        db, project_id=project_id, study_id=study_id, benchmark_id=benchmark_id
    )

    return db_benchmark_result


@router.delete("/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}/results/")
async def delete_benchmark_result(
    project_id,
    study_id,
    benchmark_id,
    db: Session = Depends(depends.get_db),
    _: APIKey = Depends(check_access_token),
):

    try:
        BenchmarkResultCRUD.delete(db, project_id, study_id, benchmark_id)
        db.commit()

    except Exception as e:

        db.rollback()
        raise e
