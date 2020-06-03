from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.forcefield import ParameterCRUD
from nonbonded.library.models.forcefield import Parameter


def test_create(db: Session):

    parameter = Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="epsilon")

    db_parameter = ParameterCRUD.create(db, parameter)
    db.add(db_parameter)
    db.commit()

    assert db.query(models.Parameter.id).count() == 1


def test_duplicate_separate_commits(db: Session):

    parameter = Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="epsilon")

    db_parameter = ParameterCRUD.create(db, parameter)
    db.add(db_parameter)
    db.commit()

    db_parameter = ParameterCRUD.create(db, parameter)
    db.add(db_parameter)
    db.commit()

    assert db.query(models.Parameter.id).count() == 1


def test_duplicate_same_commit(db: Session):

    parameter = Parameter(handler_type="vdW", smirks="[#6:1]", attribute_name="epsilon")

    db_parameter = ParameterCRUD.create(db, parameter)
    db.add(db_parameter)

    db_parameter_2 = ParameterCRUD.create(db, parameter)
    db.add(db_parameter_2)

    db.commit()

    assert db.query(models.Parameter.id).count() == 1
