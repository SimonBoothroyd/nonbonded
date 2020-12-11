from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models.datasets import (
    DataSet,
    DataSetCollection,
    QCDataSet,
    QCDataSetCollection,
)
from nonbonded.tests.backend.api.utilities import (
    BaseTestEndpoints,
    commit_data_set,
    commit_qc_data_set,
)
from nonbonded.tests.utilities.comparison import compare_pydantic_models
from nonbonded.tests.utilities.factory import create_data_set, create_qc_data_set


class TestDataSetEndpoints(BaseTestEndpoints):
    @classmethod
    def _rest_class(cls):
        return DataSet

    @classmethod
    def _create_model(cls, db, create_dependencies=True):
        data_set = create_data_set("data-set-1")
        data_set.entries[0].id = 1
        return data_set, {"data_set_id": data_set.id}

    @classmethod
    def _perturb_model(cls, model):
        model.description = "Updated"

    @classmethod
    def _commit_model(cls, db):
        data_set = commit_data_set(db)
        return data_set, {"data_set_id": data_set.id}

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.DataSet.id).count()

    def test_get_all(self, rest_client: TestClient, db: Session):

        data_set = commit_data_set(db)
        rest_data_collection = DataSetCollection.from_rest(requests_class=rest_client)

        assert rest_data_collection is not None
        assert len(rest_data_collection.data_sets) == 1

        assert rest_data_collection.metadata is not None
        assert rest_data_collection.metadata.skip == 0
        assert rest_data_collection.metadata.limit == 100
        assert rest_data_collection.metadata.total_records == 1

        compare_pydantic_models(data_set, rest_data_collection.data_sets[0])


class TestQCDataSetEndpoints(BaseTestEndpoints):
    @classmethod
    def _rest_class(cls):
        return QCDataSet

    @classmethod
    def _create_model(cls, db, create_dependencies=True):
        qc_data_set = create_qc_data_set("qc-data-set-1")
        return qc_data_set, {"qc_data_set_id": qc_data_set.id}

    @classmethod
    def _perturb_model(cls, model):
        model.description = "Updated"

    @classmethod
    def _commit_model(cls, db):
        qc_data_set = commit_qc_data_set(db)
        return qc_data_set, {"qc_data_set_id": qc_data_set.id}

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.QCDataSet.id).count()

    def test_get_all(self, rest_client: TestClient, db: Session):

        qc_data_set = commit_qc_data_set(db)
        rest_qc_data_set_collection = QCDataSetCollection.from_rest(
            requests_class=rest_client
        )

        assert rest_qc_data_set_collection is not None
        assert len(rest_qc_data_set_collection.data_sets) == 1

        assert rest_qc_data_set_collection.metadata is not None
        assert rest_qc_data_set_collection.metadata.skip == 0
        assert rest_qc_data_set_collection.metadata.limit == 100
        assert rest_qc_data_set_collection.metadata.total_records == 1

        compare_pydantic_models(qc_data_set, rest_qc_data_set_collection.data_sets[0])
