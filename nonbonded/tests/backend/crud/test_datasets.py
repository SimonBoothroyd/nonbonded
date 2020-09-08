from typing import List

import pytest
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.datasets import DataSetCRUD, MoleculeSetCRUD
from nonbonded.backend.database.crud.projects import BenchmarkCRUD, OptimizationCRUD
from nonbonded.backend.database.utilities.exceptions import (
    DataSetExistsError,
    DataSetNotFoundError,
    MoleculeSetExistsError,
    MoleculeSetNotFoundError,
)
from nonbonded.tests.backend.crud.utilities import BaseCRUDTest, create_dependencies
from nonbonded.tests.utilities.factory import create_data_set, create_molecule_set


class TestDataSetCRUD(BaseCRUDTest):
    @classmethod
    def crud_class(cls):
        return DataSetCRUD

    @classmethod
    def dependencies(cls):
        return []

    @classmethod
    def create_model(cls, include_children=False, index=1):
        data_set = create_data_set(f"data-set-{index}")
        data_set.entries[0].id = index
        return data_set

    @classmethod
    def not_found_error(cls):
        return DataSetNotFoundError

    @classmethod
    def already_exists_error(cls):
        return DataSetExistsError

    @classmethod
    def model_to_read_kwargs(cls, model):
        return {"data_set_id": model.id}

    @classmethod
    def model_to_read_all_kwargs(cls, model):
        return {}

    @classmethod
    def check_has_deleted(cls, db: Session):

        from nonbonded.backend.database.models.datasets import author_base_sets_table

        assert db.query(models.Component.id).count() == 0
        assert db.query(models.DataSetEntry.id).count() == 0
        assert db.query(models.DataSet).count() == 0
        assert db.query(author_base_sets_table).count() == 0

    @pytest.mark.parametrize(
        "create_dependant, delete_dependant",
        [
            (
                lambda db: create_dependencies(db, ["evaluator-target"]),
                lambda db: OptimizationCRUD.delete(
                    db,
                    "project-1",
                    "study-1",
                    "optimization-1",
                ),
            ),
            (
                lambda db: create_dependencies(db, ["benchmark"]),
                lambda db: BenchmarkCRUD.delete(
                    db, "project-1", "study-1", "benchmark-1"
                ),
            ),
        ],
    )
    def test_delete_with_dependent(
        self, db: Session, create_dependant, delete_dependant
    ):
        super(TestDataSetCRUD, self).test_delete_with_dependent(
            db, create_dependant, delete_dependant
        )

    @pytest.mark.skip("Data sets cannot be updated yet.")
    def test_update(self, db: Session, perturbation, database_checks, expected_raise):
        pass

    @pytest.mark.skip("Data sets cannot be updated yet.")
    def test_update_not_found(self, db: Session):
        pass

    @pytest.mark.skip("Data sets  do not have any dependencies.")
    def test_missing_dependencies(
        self, db: Session, dependencies: List[str], expected_error
    ):
        pass


class TestMoleculeSetCRUD(BaseCRUDTest):
    @classmethod
    def crud_class(cls):
        return MoleculeSetCRUD

    @classmethod
    def dependencies(cls):
        return []

    @classmethod
    def create_model(cls, include_children=False, index=1):
        return create_molecule_set(f"molecule-set-{index}")

    @classmethod
    def not_found_error(cls):
        return MoleculeSetNotFoundError

    @classmethod
    def already_exists_error(cls):
        return MoleculeSetExistsError

    @classmethod
    def model_to_read_kwargs(cls, model):
        return {"molecule_set_id": model.id}

    @classmethod
    def model_to_read_all_kwargs(cls, model):
        return {}

    @classmethod
    def check_has_deleted(cls, db: Session):

        from nonbonded.backend.database.models.datasets import author_base_sets_table

        assert db.query(models.Molecule.id).count() == 0
        assert db.query(models.MoleculeSet.id).count() == 0
        assert db.query(author_base_sets_table).count() == 0

    @pytest.mark.parametrize(
        "create_dependant, delete_dependant",
        [
            (
                lambda db: create_dependencies(db, ["recharge-target"]),
                lambda db: OptimizationCRUD.delete(
                    db,
                    "project-1",
                    "study-1",
                    "optimization-1",
                ),
            ),
        ],
    )
    def test_delete_with_dependent(
        self, db: Session, create_dependant, delete_dependant
    ):
        super(TestMoleculeSetCRUD, self).test_delete_with_dependent(
            db, create_dependant, delete_dependant
        )

    @pytest.mark.skip("Molecule sets cannot be updated yet.")
    def test_update(self, db: Session, perturbation, database_checks, expected_raise):
        pass

    @pytest.mark.skip("Molecule sets cannot be updated yet.")
    def test_update_not_found(self, db: Session):
        pass

    @pytest.mark.skip("Molecule sets  do not have any dependencies.")
    def test_missing_dependencies(
        self, db: Session, dependencies: List[str], expected_error
    ):
        pass
