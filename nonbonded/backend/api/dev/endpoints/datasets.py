import logging

from fastapi import APIRouter, Depends
from fastapi.openapi.models import APIKey
from sqlalchemy.orm import Session

from nonbonded.backend.api import depends
from nonbonded.backend.api.base import BaseCRUDEndpoint
from nonbonded.backend.core.security import check_access_token
from nonbonded.backend.database.crud.datasets import DataSetCRUD, QCDataSetCRUD
from nonbonded.library.models.datasets import (
    DataSet,
    DataSetCollection,
    QCDataSet,
    QCDataSetCollection,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class DataSetEndpoints(BaseCRUDEndpoint):
    @classmethod
    def _crud_class(cls):
        return DataSetCRUD

    @staticmethod
    @router.get("/phys-prop/", response_model=DataSetCollection)
    async def get_all(
        db: Session = Depends(depends.get_db),
        skip: int = 0,
        limit: int = 100,
        children: bool = True,
    ):
        db_data_sets = DataSetCRUD.read_all(
            db, skip=skip, limit=limit, include_children=children
        )
        return {"data_sets": db_data_sets}

    @staticmethod
    @router.get("/phys-prop/{data_set_id}")
    async def get(data_set_id, db: Session = Depends(depends.get_db)):
        return DataSetEndpoints._read_function(db, data_set_id=data_set_id)

    @staticmethod
    @router.post("/phys-prop/")
    async def post_data_set(
        data_set: DataSet,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return DataSetEndpoints._post(db, data_set)

    @staticmethod
    @router.delete("/phys-prop/{data_set_id}")
    async def delete_data_set(
        data_set_id,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return DataSetEndpoints._delete(db, data_set_id=data_set_id)


class QCDataSetEndpoints(BaseCRUDEndpoint):
    @classmethod
    def _crud_class(cls):
        return QCDataSetCRUD

    @staticmethod
    @router.get("/qc/", response_model=QCDataSetCollection)
    async def get_all(
        db: Session = Depends(depends.get_db),
        skip: int = 0,
        limit: int = 100,
        children: bool = True,
    ):
        db_qc_data_sets = QCDataSetCRUD.read_all(
            db, skip=skip, limit=limit, include_children=children
        )
        return {"data_sets": db_qc_data_sets}

    @staticmethod
    @router.get("/qc/{qc_data_set_id}")
    async def get(qc_data_set_id, db: Session = Depends(depends.get_db)):
        return QCDataSetEndpoints._read_function(db, qc_data_set_id=qc_data_set_id)

    @staticmethod
    @router.post("/qc/")
    async def post_qc_data_set(
        qc_data_set: QCDataSet,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return QCDataSetEndpoints._post(db, qc_data_set)

    @staticmethod
    @router.delete("/qc/{qc_data_set_id}")
    async def delete_qc_data_set(
        qc_data_set_id,
        db: Session = Depends(depends.get_db),
        _: APIKey = Depends(check_access_token),
    ):
        return QCDataSetEndpoints._delete(db, qc_data_set_id=qc_data_set_id)
