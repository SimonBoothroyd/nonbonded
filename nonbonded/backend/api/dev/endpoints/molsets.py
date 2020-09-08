import logging

from fastapi import APIRouter, Depends
from fastapi.openapi.models import APIKey
from sqlalchemy.orm import Session

from nonbonded.backend.api import depends
from nonbonded.backend.api.base import BaseCRUDEndpoint
from nonbonded.backend.core.security import check_access_token
from nonbonded.backend.database.crud.datasets import MoleculeSetCRUD
from nonbonded.library.models.datasets import MoleculeSet, MoleculeSetCollection

logger = logging.getLogger(__name__)
router = APIRouter()


class MoleculeSetEndpoints(BaseCRUDEndpoint):
    @classmethod
    def _crud_class(cls):
        return MoleculeSetCRUD

    @staticmethod
    @router.get("/", response_model=MoleculeSetCollection)
    async def get_all(
        db: Session = Depends(depends.get_db),
        skip: int = 0,
        limit: int = 100,
    ):
        db_molecule_sets = MoleculeSetCRUD.read_all(db, skip=skip, limit=limit)
        return {"molecule_sets": db_molecule_sets}

    @staticmethod
    @router.get("/{molecule_set_id}")
    async def get(molecule_set_id, db: Session = Depends(depends.get_db)):
        return MoleculeSetEndpoints._read_function(db, molecule_set_id=molecule_set_id)

    @staticmethod
    @router.post("/")
    async def post_molecule_set(
        molecule_set: MoleculeSet,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return MoleculeSetEndpoints._post(db, molecule_set)

    @staticmethod
    @router.delete("/{molecule_set_id}")
    async def delete_molecule_set(
        molecule_set_id,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return MoleculeSetEndpoints._delete(db, molecule_set_id=molecule_set_id)
