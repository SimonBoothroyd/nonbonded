from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from nonbonded.backend.api import depends
from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.library.models.datasets import DataSet, DataSetCollection

router = APIRouter()


@router.get("/", response_model=DataSetCollection)
async def get_projects(
    project_id: Optional[str] = None,
    study_id: Optional[str] = None,
    optimization_id: Optional[str] = None,
    db: Session = Depends(depends.get_db),
):

    db_projects = DataSetCRUD.read_by_identifiers(
        db, project_id, study_id, optimization_id
    )

    return {"data_sets": db_projects}


@router.post("/")
async def post_project(data_set: DataSet, db: Session = Depends(depends.get_db)):

    db_data_set = DataSetCRUD.read_by_identifiers(
        db,
        data_set.project_identifier,
        data_set.study_identifier,
        data_set.optimization_identifier,
    )

    if db_data_set and len(db_data_set) > 0:
        raise HTTPException(status_code=400, detail="Data set already registered")

    return DataSetCRUD.create(db, data_set)
