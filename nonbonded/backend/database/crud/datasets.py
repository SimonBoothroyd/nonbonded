from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.authors import AuthorCRUD
from nonbonded.library.models import datasets


class DataSetEntryCRUD:

    @staticmethod
    def create(
        data_set_entry: datasets.DataSetEntry,
    ) -> models.DataSetEntry:

        # noinspection PyTypeChecker
        db_data_set_entry = models.DataSetEntry(
            property_type=data_set_entry.property_type,
            temperature=data_set_entry.temperature,
            pressure=data_set_entry.pressure,
            phase=data_set_entry.phase,
            unit=data_set_entry.unit,
            value=data_set_entry.value,
            std_error=data_set_entry.std_error,
            doi=data_set_entry.doi,
            components=[
                models.Component(
                    smiles=component.smiles,
                    mole_fraction=component.mole_fraction,
                    exact_amount=component.exact_amount,
                    role=component.role
                )
                for component in data_set_entry.components
            ],
        )

        return db_data_set_entry

    @staticmethod
    def db_to_model(
        db_data_set_entry: models.DataSetEntry,
    ) -> datasets.DataSetEntry:

        data_set_entry = datasets.DataSetEntry(
            property_type=db_data_set_entry.property_type,
            temperature=db_data_set_entry.temperature,
            pressure=db_data_set_entry.pressure,
            phase=db_data_set_entry.phase,
            unit=db_data_set_entry.unit,
            value=db_data_set_entry.value,
            std_error=db_data_set_entry.std_error,
            doi=db_data_set_entry.doi,
            components=db_data_set_entry.components,
        )

        return data_set_entry


class DataSetCRUD:

    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100):

        data_sets = db.query(models.DataSet).offset(skip).limit(limit).all()
        return data_sets

    @staticmethod
    def read_by_identifier(db: Session, identifier: str):

        db_data_set = db.query(models.DataSet).filter(models.DataSet.id == identifier).first()

        if db_data_set is None:
            return

        return DataSetCRUD.db_to_model(db_data_set)

    @staticmethod
    def create(db: Session, data_set: datasets.DataSet) -> models.DataSet:

        # noinspection PyTypeChecker
        db_data_set = models.DataSet(
            id=data_set.id,
            description=data_set.description,
            authors=[AuthorCRUD.create(db, author) for author in data_set.authors],
            entries=[DataSetEntryCRUD.create(entry) for entry in data_set.entries]
        )

        db.add(db_data_set)
        db.commit()
        db.refresh(db_data_set)

        return db_data_set

    @staticmethod
    def db_to_model(db_data_set: models.DataSet) -> datasets.DataSet:

        # noinspection PyTypeChecker
        data_set = datasets.DataSet(
            identifier=db_data_set.id,
            description=db_data_set.description,
            entries=[
                DataSetEntryCRUD.db_to_model(entry) for entry in db_data_set.entries
            ],
            authors=db_data_set.authors
        )

        return data_set
