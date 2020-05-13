import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from nonbonded.backend.api import depends
from nonbonded.backend.database.crud.projects import ProjectCRUD
from nonbonded.library.models.projects import Project, ProjectCollection

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

    db_project = ProjectCRUD.read_by_identifier(db, identifier=project.identifier)

    if db_project:
        raise HTTPException(status_code=400, detail="Project already registered")

    try:
        db_project = ProjectCRUD.create(db=db, project=project)

        db.add(db_project)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return db_project


@router.get("/{project_id}")
async def get_project(project_id, db: Session = Depends(depends.get_db)):

    db_project = ProjectCRUD.read_by_identifier(db, identifier=project_id)

    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    return db_project
