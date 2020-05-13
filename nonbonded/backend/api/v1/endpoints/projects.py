import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from nonbonded.backend.api import depends
from nonbonded.backend.database.crud.projects import ProjectCRUD, StudyCRUD, \
    OptimizationCRUD, BenchmarkCRUD
from nonbonded.library.models.projects import Project, ProjectCollection, \
    StudyCollection, OptimizationCollection, Study, BenchmarkCollection

router = APIRouter()

PROJECT_DIRECTORY = os.path.join("rest", "projects")


@router.get("/", response_model=ProjectCollection)
async def get_projects(
    skip: int = 0, limit: int = 100, db: Session = Depends(depends.get_db)
):

    db_projects = ProjectCRUD.read_all(db, skip=skip, limit=limit)
    return {"projects": db_projects}


@router.post("/")
async def post_project(project: Project, db: Session = Depends(depends.get_db)):

    db_project = ProjectCRUD.read_by_identifier(db, identifier=project.id)

    if db_project:

        raise HTTPException(
            status_code=400, detail=f"A project with id={project.id} already exists"
        )

    db_project = ProjectCRUD.create(db=db, project=project)
    return db_project


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id, db: Session = Depends(depends.get_db)):

    db_project = ProjectCRUD.read_by_identifier(db, identifier=project_id)

    if not db_project:

        raise HTTPException(
            status_code=404, detail=f"Project with id={project_id} not found."
        )

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

    if not db_study:

        raise HTTPException(
            status_code=404,
            detail=f"Study with id={study_id} and parent project id={project_id} not "
            f"found."
        )

    return db_study


@router.get(
    "/{project_id}/studies/{study_id}/optimizations",
    response_model=OptimizationCollection
)
async def get_studies(project_id, study_id, db: Session = Depends(depends.get_db)):

    db_optimizations = OptimizationCRUD.read_all(
        db, project_id=project_id, study_id=study_id
    )

    return {"optimizations": db_optimizations}


@router.get("/{project_id}/studies/{study_id}/optimizations/{optimization_id}",)
async def get_study(
    project_id, study_id, optimization_id, db: Session = Depends(depends.get_db)
):

    db_optimization = OptimizationCRUD.read_by_identifier(
        db, project_id=project_id, study_id=study_id, optimization_id=optimization_id
    )

    if not db_optimization:

        raise HTTPException(
            status_code=404,
            detail=f"Optimzation with id={optimization_id} and parent study "
            f"id={study_id} and parent project id={project_id} not found."
        )

    return db_optimization


@router.get(
    "/{project_id}/studies/{study_id}/benchmarks",
    response_model=BenchmarkCollection
)
async def get_studies(project_id, study_id, db: Session = Depends(depends.get_db)):

    db_benchmarks = BenchmarkCRUD.read_all(
        db, project_id=project_id, study_id=study_id
    )

    return {"benchmarks": db_benchmarks}


@router.get("/{project_id}/studies/{study_id}/benchmarks/{benchmark_id}",)
async def get_study(
    project_id, study_id, benchmark_id, db: Session = Depends(depends.get_db)
):

    db_benchmark = BenchmarkCRUD.read_by_identifier(
        db, project_id=project_id, study_id=study_id, benchmark_id=benchmark_id
    )

    if not db_benchmark:

        raise HTTPException(
            status_code=404,
            detail=f"Optimzation with id={benchmark_id} and parent study "
            f"id={study_id} and parent project id={project_id} not found."
        )

    return db_benchmark
