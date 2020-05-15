from fastapi import APIRouter, Depends
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

    try:
        db_data_set = DataSetCRUD.create(db, data_set)

        db.add(db_data_set)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return db_data_set


@router.get("/{data_set_id}")
async def get_data_set(data_set_id, db: Session = Depends(depends.get_db)):

    db_project = DataSetCRUD.read_by_identifier(db, data_set_id)
    return db_project
