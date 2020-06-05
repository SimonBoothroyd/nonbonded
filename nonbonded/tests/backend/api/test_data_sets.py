from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models.datasets import DataSet, DataSetCollection
from nonbonded.tests.backend.api.utilities import BaseTestEndpoints
from nonbonded.tests.backend.crud.utilities.commit import commit_data_set
from nonbonded.tests.backend.crud.utilities.comparison import compare_data_sets
from nonbonded.tests.backend.crud.utilities.create import create_data_set


class TestDataSetEndpoints(BaseTestEndpoints):
    @classmethod
    def _rest_class(cls):
        return DataSet

    @classmethod
    def _create_model(cls, db, create_dependencies=True):
        data_set = create_data_set("data-set-1")
        return data_set, {"data_set_id": data_set.id}

    @classmethod
    def _perturb_model(cls, model):
        model.description = "Updated"

    @classmethod
    def _commit_model(cls, db):
        data_set = commit_data_set(db)
        return data_set, {"data_set_id": data_set.id}

    @classmethod
    def _comparison_function(cls):
        return compare_data_sets

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.DataSet.id).count()

    def test_get_all(self, rest_client: TestClient, rest_db: Session):

        data_set = commit_data_set(rest_db)
        rest_data_collection = DataSetCollection.from_rest(rest_client)

        assert rest_data_collection is not None
        assert len(rest_data_collection.data_sets) == 1

        compare_data_sets(data_set, rest_data_collection.data_sets[0])
