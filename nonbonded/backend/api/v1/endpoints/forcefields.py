from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from nonbonded.backend.api import depends
from nonbonded.backend.database.crud.forcefield import RefitForceFieldCRUD
from nonbonded.library.models.forcefield import (
    RefitForceField,
    RefitForceFieldCollection,
)

router = APIRouter()


@router.get("/", response_model=RefitForceFieldCollection)
async def get_force_fields(
    project_id: str,
    study_id: str,
    optimization_id: str,
    db: Session = Depends(depends.get_db),
):

    db_force_field = RefitForceFieldCRUD.read_by_optimization(
        db, project_id, study_id, optimization_id
    )
    return db_force_field


@router.post("/")
async def post_project(
    refit_force_field: RefitForceField, db: Session = Depends(depends.get_db)
):

    try:
        db_force_field = RefitForceFieldCRUD.create(
            db=db, refit_force_field=refit_force_field
        )

        db.add(db_force_field)
        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    return db_force_field


@router.delete("/{force_field_id}")
async def delete_force_field(
    force_field_id: int, db: Session = Depends(depends.get_db),
):

    try:
        db_force_field = RefitForceFieldCRUD.delete(db, force_field_id)

        db.commit()

    except Exception as e:

        db.rollback()
        raise e

    return db_force_field
