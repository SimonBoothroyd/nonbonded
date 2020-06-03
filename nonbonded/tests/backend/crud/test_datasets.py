import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.datasets import DataSetCRUD
from nonbonded.backend.database.utilities.exceptions import (
    DataSetExistsError,
    DataSetNotFoundError,
)
from nonbonded.tests.backend.crud.utilities import compare_data_sets, create_data_set


def test_create_read(db: Session):
    """Test that data sets can be successfully created, and then
    read back out again while maintaining the integrity of the data.
    """

    data_set_id = "data-set-1"
    data_set = create_data_set(data_set_id)

    db_data_set = DataSetCRUD.create(db, data_set)
    db.add(db_data_set)
    db.commit()

    retrieved_sets = DataSetCRUD.read_all(db)
    assert len(retrieved_sets) == 1

    db_retrieved_set = retrieved_sets[0]
    compare_data_sets(data_set, db_retrieved_set)
    compare_data_sets(data_set, DataSetCRUD.db_to_model(db_retrieved_set))

    db_retrieved_set = DataSetCRUD.read(db, data_set_id)
    compare_data_sets(data_set, db_retrieved_set)
    compare_data_sets(data_set, DataSetCRUD.db_to_model(db_retrieved_set))


def test_pagination(db: Session):
    """Test that the limit and skip options to read_all have been implemented
    correctly.
    """

    data_set_1 = create_data_set("data-set-1")

    db.add(DataSetCRUD.create(db, data_set_1))
    db.commit()

    data_set_2 = create_data_set("data-set-2")

    db.add(DataSetCRUD.create(db, data_set_2))
    db.commit()

    retrieved_sets = DataSetCRUD.read_all(db, skip=0, limit=1)
    assert len(retrieved_sets) == 1
    compare_data_sets(data_set_1, retrieved_sets[0])

    retrieved_sets = DataSetCRUD.read_all(db, skip=1, limit=1)
    assert len(retrieved_sets) == 1
    compare_data_sets(data_set_2, retrieved_sets[0])


def test_data_set_exists_exception(db: Session):

    # Test adding duplicates in the separate commits.
    data_set_id = "data-set-2"
    data_set = create_data_set(data_set_id)

    db_data_set_1 = DataSetCRUD.create(db, data_set)
    db.add(db_data_set_1)
    db.commit()

    with pytest.raises(DataSetExistsError):
        DataSetCRUD.create(db, data_set)


def test_duplicate_id_integrity_error(db: Session):

    # Test adding duplicates in the same commit.
    data_set_id = "data-set-1"
    data_set = create_data_set(data_set_id)

    db_data_set_1 = DataSetCRUD.create(db, data_set)
    db_data_set_2 = DataSetCRUD.create(db, data_set)

    db.add(db_data_set_1)
    db.add(db_data_set_2)

    with pytest.raises(IntegrityError):
        db.commit()


def test_delete_data_set(db: Session):

    from nonbonded.backend.database.models.datasets import author_data_sets_table

    # Test adding duplicates in the same commit.
    data_set_id = "data-set-1"
    data_set = create_data_set(data_set_id)

    db_data_set = DataSetCRUD.create(db, data_set)
    db.add(db_data_set)
    db.commit()

    assert db.query(models.Component.id).count() == 2
    assert db.query(models.DataSetEntry.id).count() == 1
    assert db.query(models.DataSet).count() == 1
    assert db.query(author_data_sets_table).count() == 1

    DataSetCRUD.delete(db, data_set_id)
    db.commit()

    assert db.query(models.Component.id).count() == 0
    assert db.query(models.DataSetEntry.id).count() == 0
    assert db.query(models.DataSet).count() == 0
    assert db.query(author_data_sets_table).count() == 0


def test_delete_data_set_not_found(db: Session):

    with pytest.raises(DataSetNotFoundError):
        DataSetCRUD.delete(db, "data_set_id")
