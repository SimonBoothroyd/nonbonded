import abc
from typing import TypeVar

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query, Session

Base = declarative_base()

T = TypeVar("T")


class UniqueMixin:
    """A base class for records which should be unique in the
    database.

    Notes
    -----
    This class is based upon the ``sqlalchemy`` example `based here <
    https://github.com/sqlalchemy/sqlalchemy/wiki/UniqueObject>`_.
    """

    @classmethod
    @abc.abstractmethod
    def _hash(cls, db_instance: T) -> int:
        """Returns the hash of the instance that this record represents.

        Parameters
        ----------
        db_instance
            The instance to hash.

        Returns
        -------
            The hashed instance.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def _query(cls, db: Session, db_instance: T) -> Query:
        """Returns a query which should find existing copies of an instance.

        Parameters
        ----------
        db
            The current database session.
        db_instance
            The instance to query for.

        Returns
        -------
            The constructed query.
        """
        raise NotImplementedError()

    @classmethod
    def unique(cls, db: Session, db_instance: T) -> T:
        """Creates a new database object from the specified instance if it
        does not already exist on the database, otherwise the existing
        instance is returned.

        Parameters
        ----------
        db
            The current database session.
        db_instance
            The instance to query for and add if not already in the database.

        Returns
        -------
            The instance in the database. This will be an existing instance if already
            present, or the provided instance if not.
        """

        cache = getattr(db, "_unique_cache", None)

        if cache is None:
            db._unique_cache = cache = {}

        key = (cls, cls._hash(db_instance))

        if key in cache:
            return cache[key]

        with db.no_autoflush:

            existing_instance = cls._query(db, db_instance).first()

            if not existing_instance:

                existing_instance = db_instance
                db.add(existing_instance)

        cache[key] = existing_instance
        return existing_instance
