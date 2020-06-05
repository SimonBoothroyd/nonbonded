import abc
from typing import Callable, TypeVar

from sqlalchemy.orm import Session

from nonbonded.backend.database.crud.crud import CRUDInterface

S = TypeVar("S", bound="BaseORM")
T = TypeVar("T", bound="Base")


class BaseCRUDEndpoint(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def _crud_class(cls) -> CRUDInterface:
        raise NotImplementedError()

    @classmethod
    def _create_function(cls, db: Session, model: S) -> T:
        return cls._crud_class().create(db, model)

    @classmethod
    def _read_function(cls, db: Session, **keys: str) -> T:
        return cls._crud_class().read(db, **keys)

    @classmethod
    def _update_function(cls, db: Session, model: S) -> T:
        return cls._crud_class().update(db, model)

    @classmethod
    def _delete_function(cls, db: Session, **keys: str) -> T:
        return cls._crud_class().delete(db, **keys)

    @classmethod
    def _db_to_model(cls, db_model: T) -> S:
        return cls._crud_class().db_to_model(db_model)

    @classmethod
    def _create_update(
        cls,
        db: Session,
        model: S,
        update_function: Callable[[Session, S], T],
        add_model: bool,
    ) -> S:
        """A generic method for handling any kind create or update endpoints
        such as post or put.


        Parameters
        ----------
        db
            The current database session.
        model
            The posted model
        update_function
            The method which will map the posted model into a database
            model either by creating a model in the database, or updating
            an existing one.
        add_model
            Whether database model returned by the `update_function` needs to be
            added to the session.

        Returns
        -------
            The library representation of the model which has been stored in
            the database.
        """
        try:
            db_model = update_function(db, model)

            if add_model:
                db.add(db_model)

            db.commit()

        except Exception as e:
            db.rollback()
            raise e

        return cls._db_to_model(db_model)

    @classmethod
    def _post(cls, db: Session, model: S) -> S:
        """Handle post requests from the client by attempting to add
        the posted model into the database.

        Parameters
        ----------
        db
            The current database session.
        model
            The posted model

        Returns
        -------
            The library representation of the model which has been stored in
            the database.
        """
        return cls._create_update(db, model, cls._create_function, True)

    @classmethod
    def _put(cls, db: Session, model: S) -> S:
        """Handle put requests from the client by attempting to update
        an existing database model to match the posted model.

        Parameters
        ----------
        db
            The current database session.
        model
            The posted model

        Returns
        -------
            The library representation of the model which has been stored in
            the database.
        """
        return cls._create_update(db, model, cls._update_function, False)

    @classmethod
    def _delete(cls, db: Session, **keys: str):
        """Handle delete requests from the client by attempting to remove
        an existing database model which matches the provided model from the
        database.

        Parameters
        ----------
        db
            The current database session.
        model_ids
            The keys which uniquely identify the model to delete.
        """

        try:
            cls._delete_function(db, **keys)
            db.commit()

        except Exception as e:

            db.rollback()
            raise e
