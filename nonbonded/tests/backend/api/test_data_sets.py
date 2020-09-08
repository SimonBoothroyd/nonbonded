from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models.datasets import (
    DataSet,
    DataSetCollection,
    MoleculeSet,
    MoleculeSetCollection,
)
from nonbonded.tests.backend.api.utilities import (
    BaseTestEndpoints,
    commit_data_set,
    commit_molecule_set,
)
from nonbonded.tests.utilities.comparison import compare_pydantic_models
from nonbonded.tests.utilities.factory import create_data_set, create_molecule_set


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
        rest_data_collection = DataSetCollection.from_rest(rest_client)

        assert rest_data_collection is not None
        assert len(rest_data_collection.data_sets) == 1

        compare_pydantic_models(data_set, rest_data_collection.data_sets[0])


class TestMoleculeSetEndpoints(BaseTestEndpoints):
    @classmethod
    def _rest_class(cls):
        return MoleculeSet

    @classmethod
    def _create_model(cls, db, create_dependencies=True):
        molecule_set = create_molecule_set("molecule-set-1")
        return molecule_set, {"molecule_set_id": molecule_set.id}

    @classmethod
    def _perturb_model(cls, model):
        model.description = "Updated"

    @classmethod
    def _commit_model(cls, db):
        molecule_set = commit_molecule_set(db)
        return molecule_set, {"molecule_set_id": molecule_set.id}

    @classmethod
    def _n_db_models(cls, db: Session) -> int:
        return db.query(models.MoleculeSet.id).count()

    def test_get_all(self, rest_client: TestClient, db: Session):

        molecule_set = commit_molecule_set(db)
        rest_molecule_collection = MoleculeSetCollection.from_rest(rest_client)

        assert rest_molecule_collection is not None
        assert len(rest_molecule_collection.molecule_sets) == 1

        compare_pydantic_models(molecule_set, rest_molecule_collection.molecule_sets[0])
