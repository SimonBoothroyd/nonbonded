from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from nonbonded.backend.api import depends
from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.library.models.datasets import DataSet, DataSetCollection

router = APIRouter()


@router.get("/", response_model=DataSetCollection)
async def get_data_sets(
    db: Session = Depends(depends.get_db), skip: int = 0, limit: int = 100,
):

    db_projects = DataSetCRUD.read_all(db, skip=skip, limit=limit)
    return {"data_sets": db_projects}


@router.post("/")
async def post_data_set(data_set: DataSet, db: Session = Depends(depends.get_db)):

    db_data_set = DataSetCRUD.read_by_identifier(db, data_set.id)

    if db_data_set and len(db_data_set) > 0:

        raise HTTPException(
            status_code=400,
            detail=f"Data set with id={data_set.id} already registered.",
        )

    db_data_set = DataSetCRUD.create(db, data_set)
    return db_data_set


@router.get("/{data_set_id}")
async def get_data_set(data_set_id, db: Session = Depends(depends.get_db)):

    db_project = DataSetCRUD.read_by_identifier(db, identifier=data_set_id)

    if not db_project:

        raise HTTPException(
            status_code=404, detail=f"Data set with id={data_set_id} not found."
        )

    return db_project
