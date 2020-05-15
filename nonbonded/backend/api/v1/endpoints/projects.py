from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from nonbonded.backend.api import depends
from nonbonded.backend.database.crud.projects import (
    BenchmarkCRUD,
    OptimizationCRUD,
    ProjectCRUD,
    StudyCRUD,
)
from nonbonded.library.models.projects import (
    BenchmarkCollection,
    OptimizationCollection,
    Project,
    ProjectCollection,
    Study,
    StudyCollection,
)

router = APIRouter()


@router.get("/", response_model=ProjectCollection)
async def get_projects(
    skip: int = 0, limit: int = 100, db: Session = Depends(depends.get_db)
):

    db_projects = ProjectCRUD.read_all(db, skip=skip, limit=limit)
    return {"projects": db_projects}


@router.post("/")
async def post_project(project: Project, db: Session = Depends(depends.get_db)):

    try:
        db_project = ProjectCRUD.create(db=db, project=project)

        db.add(db_project)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return db_project


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id, db: Session = Depends(depends.get_db)):

    db_project = ProjectCRUD.read_by_identifier(db, project_id)
    return db_project


@router.get("/{project_id}/studies", response_model=StudyCollection)
async def get_studies(project_id, db: Session = Depends(depends.get_db)):

    db_studies = StudyCRUD.read_all(db, project_id=project_id)
    return {"studies": db_studies}


@router.get("/{project_id}/studies/{study_id}", response_model=Study)
async def get_study(project_id, study_id, db: Session = Depends(depends.get_db)):

    db_study = StudyCRUD.read_by_identifier(
        db, study_id=study_id, project_id=project_id
    )

    return db_study


@router.get(
    "/{project_id}/studies/{study_id}/optimizations",
    response_model=OptimizationCollection,
)
async def get_optimizations(
    project_id, study_id, db: Session = Depends(depends.get_db)
):

    db_optimizations = OptimizationCRUD.read_all(
        db, project_id=project_id, study_id=study_id
    )

    return {"optimizations": db_optimizations}


@router.get("/{project_id}/studies/{study_id}/optimizations/{optimization_id}",)
async def get_optimization(
    project_id, study_id, optimization_id, db: Session = Depends(depends.get_db)
):

    db_optimization = OptimizationCRUD.read_by_identifier(
        db, project_id=project_id, study_id=study_id, optimization_id=optimization_id
    )

    return db_optimization


@router.get(
    "/{project_id}/studies/{study_id}/benchmarks", response_model=BenchmarkCollection
)
async def get_benchmarks(project_id, study_id, db: Session = Depends(depends.get_db)):

    db_benchmarks = BenchmarkCRUD.read_all(db, project_id=project_id, study_id=study_id)
    return {"benchmarks": db_benchmarks}


@router.get("/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}",)
async def get_benchmark(
    project_id, study_id, benchmark_id, db: Session = Depends(depends.get_db)
):

    db_benchmark = BenchmarkCRUD.read_by_identifier(
        db, project_id=project_id, study_id=study_id, benchmark_id=benchmark_id
    )

    return db_benchmark
