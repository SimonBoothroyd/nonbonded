from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.backend.database.crud.authors import AuthorCRUD
from nonbonded.backend.database.utilities.exceptions import (
    DataSetExistsError,
    DataSetNotFoundError,
    QCDataSetExistsError,
    QCDataSetNotFoundError,
    UnableToDeleteError,
)
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
            value=data_set_entry.value,
            std_error=data_set_entry.std_error,
            doi=data_set_entry.doi,
            components=[
                models.Component(
                    smiles=component.smiles,
                    mole_fraction=component.mole_fraction,
                    exact_amount=component.exact_amount,
                    role=component.role,
                )
                for component in data_set_entry.components
            ],
        )

        return db_data_set_entry

    @staticmethod
    def db_to_model(
        db_data_set_entry: models.DataSetEntry,
    ) -> datasets.DataSetEntry:

        # noinspection PyTypeChecker
        data_set_entry = datasets.DataSetEntry(
            id=db_data_set_entry.id,
            property_type=db_data_set_entry.property_type,
            temperature=db_data_set_entry.temperature,
            pressure=db_data_set_entry.pressure,
            phase=db_data_set_entry.phase,
            value=db_data_set_entry.value,
            std_error=db_data_set_entry.std_error,
            doi=db_data_set_entry.doi,
            components=db_data_set_entry.components,
        )

        return data_set_entry


class DataSetCRUD:
    @staticmethod
    def query(db: Session, data_set_id: str):

        db_data_set = (
            db.query(models.DataSet).filter(models.DataSet.id == data_set_id).first()
        )

        return db_data_set

    @staticmethod
    def read_all(
        db: Session, skip: int = 0, limit: int = 100, include_children: bool = True
    ):

        data_sets = db.query(models.DataSet).offset(skip).limit(limit).all()
        return [DataSetCRUD.db_to_model(x, include_children) for x in data_sets]

    @staticmethod
    def read(db: Session, data_set_id: str):

        db_data_set = DataSetCRUD.query(db, data_set_id)

        if db_data_set is None:
            raise DataSetNotFoundError(data_set_id)

        return DataSetCRUD.db_to_model(db_data_set, True)

    @staticmethod
    def create(db: Session, data_set: datasets.DataSet) -> models.DataSet:

        if DataSetCRUD.query(db, data_set.id) is not None:
            raise DataSetExistsError(data_set.id)

        # noinspection PyTypeChecker
        db_data_set = models.DataSet(
            id=data_set.id,
            description=data_set.description,
            authors=[AuthorCRUD.create(db, author) for author in data_set.authors],
            entries=[DataSetEntryCRUD.create(entry) for entry in data_set.entries],
        )

        return db_data_set

    @staticmethod
    def db_to_model(
        db_data_set: models.DataSet, include_children: bool = True
    ) -> datasets.DataSet:

        # noinspection PyTypeChecker
        data_set = datasets.DataSet(
            id=db_data_set.id,
            description=db_data_set.description,
            entries=[]
            if not include_children
            else [DataSetEntryCRUD.db_to_model(entry) for entry in db_data_set.entries],
            authors=db_data_set.authors,
        )

        return data_set

    @staticmethod
    def delete(db: Session, data_set_id: str):

        db_data_set = DataSetCRUD.query(db, data_set_id)

        if not db_data_set:
            raise DataSetNotFoundError(data_set_id)

        if len(db_data_set.optimizations) > 0 or len(db_data_set.benchmarks) > 0:

            type_name = (
                "benchmark"
                if len(db_data_set.benchmarks) > 0
                else "optimization target"
            )

            raise UnableToDeleteError(
                f"This data set (id={data_set_id}) is being referenced by at least "
                f"one {type_name} and so cannot be deleted. Delete the referencing "
                f"{type_name} first and then try again."
            )

        db.delete(db_data_set)


class QCDataSetCRUD:
    @staticmethod
    def query(db: Session, qc_data_set_id: str):

        db_qc_data_set = (
            db.query(models.QCDataSet)
            .filter(models.QCDataSet.id == qc_data_set_id)
            .first()
        )

        return db_qc_data_set

    @staticmethod
    def read_all(
        db: Session, skip: int = 0, limit: int = 100, include_children: bool = True
    ):

        qc_data_sets = db.query(models.QCDataSet).offset(skip).limit(limit).all()
        return [QCDataSetCRUD.db_to_model(x, include_children) for x in qc_data_sets]

    @staticmethod
    def read(db: Session, qc_data_set_id: str):

        db_qc_data_set = QCDataSetCRUD.query(db, qc_data_set_id)

        if db_qc_data_set is None:
            raise QCDataSetNotFoundError(qc_data_set_id)

        return QCDataSetCRUD.db_to_model(db_qc_data_set)

    @staticmethod
    def create(db: Session, qc_data_set: datasets.QCDataSet) -> models.QCDataSet:

        if QCDataSetCRUD.query(db, qc_data_set.id) is not None:
            raise QCDataSetExistsError(qc_data_set.id)

        # noinspection PyTypeChecker
        db_qc_data_set = models.QCDataSet(
            id=qc_data_set.id,
            description=qc_data_set.description,
            authors=[AuthorCRUD.create(db, author) for author in qc_data_set.authors],
            entries=[
                models.QCDataSetEntry.unique(db, models.QCDataSetEntry(record_id=entry))
                for entry in qc_data_set.entries
            ],
        )

        return db_qc_data_set

    @staticmethod
    def db_to_model(
        db_qc_data_set: models.QCDataSet, include_children: bool = True
    ) -> datasets.QCDataSet:

        qc_data_set = datasets.QCDataSet(
            id=db_qc_data_set.id,
            description=db_qc_data_set.description,
            entries=[]
            if not include_children
            else [entry.record_id for entry in db_qc_data_set.entries],
            authors=db_qc_data_set.authors,
        )

        return qc_data_set

    @staticmethod
    def delete(db: Session, qc_data_set_id: str):

        db_qc_data_set = QCDataSetCRUD.query(db, qc_data_set_id)

        if not db_qc_data_set:
            raise QCDataSetNotFoundError(qc_data_set_id)

        if len(db_qc_data_set.optimizations) > 0:

            raise UnableToDeleteError(
                f"This QC data set (id={qc_data_set_id}) is being referenced by at "
                f"least one optimization target and so cannot be deleted. Delete the "
                f"referencing optimization target first and then try again."
            )

        db.delete(db_qc_data_set)
