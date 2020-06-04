import functools

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.backend.database.utilities.exceptions import (
    DataSetExistsError,
    DataSetNotFoundError,
)
from nonbonded.tests.backend.crud.utilities import (
    create_and_compare_models,
    paginate_models,
)
from nonbonded.tests.backend.crud.utilities.commit import commit_data_set
from nonbonded.tests.backend.crud.utilities.comparison import compare_data_sets
from nonbonded.tests.backend.crud.utilities.creation import create_data_set


class TestDataSetCRUD:
    def test_create_read(self, db: Session):
        """Test that data sets can be successfully created, and then
        read back out again while maintaining the integrity of the data.
        """

        data_set_id = "data-set-1"
        data_set = create_data_set(data_set_id)

        create_and_compare_models(
            db,
            data_set,
            DataSetCRUD.create,
            DataSetCRUD.read_all,
            functools.partial(DataSetCRUD.read, data_set_id=data_set_id),
            compare_data_sets,
        )

        # Make sure data_sets with duplicate ids cannot be added.
        with pytest.raises(DataSetExistsError):
            DataSetCRUD.create(db, data_set)

    def test_pagination(self, db: Session):
        """Test that the limit and skip options to read_all have been
        implemented correctly.
        """

        paginate_models(
            db=db,
            models_to_create=[
                create_data_set("data-set-1"),
                create_data_set("data-set-2"),
                create_data_set("data-set-3"),
            ],
            create_function=DataSetCRUD.create,
            read_all_function=DataSetCRUD.read_all,
            compare_function=compare_data_sets,
        )

    def test_duplicate_id(self, db: Session):

        # Test adding duplicates in the same commit.
        data_set_id = "data-set-1"
        data_set = create_data_set(data_set_id)

        db_data_set_1 = DataSetCRUD.create(db, data_set)
        db_data_set_2 = DataSetCRUD.create(db, data_set)

        db.add(db_data_set_1)
        db.add(db_data_set_2)

        with pytest.raises(IntegrityError):
            db.commit()

    def test_delete(self, db: Session):
        """Test that data sets can be fully deleted."""

        from nonbonded.backend.database.models.datasets import author_data_sets_table

        # Test adding duplicates in the same commit.
        data_set = commit_data_set(db)

        assert db.query(models.Component.id).count() == 2
        assert db.query(models.DataSetEntry.id).count() == 1
        assert db.query(models.DataSet).count() == 1
        assert db.query(author_data_sets_table).count() == 1

        DataSetCRUD.delete(db, data_set.id)
        db.commit()

        assert db.query(models.Component.id).count() == 0
        assert db.query(models.DataSetEntry.id).count() == 0
        assert db.query(models.DataSet).count() == 0
        assert db.query(author_data_sets_table).count() == 0

    def test_delete_not_found(self, db: Session):

        with pytest.raises(DataSetNotFoundError):
            DataSetCRUD.delete(db, "data_set_id")
