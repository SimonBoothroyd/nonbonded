import abc
from typing import Optional, TypeVar

from sqlalchemy.orm import Session

S = TypeVar("S", bound="BaseORM")
T = TypeVar("T", bound="Base")


class CRUDInterface(abc.ABC):
    """A base class for all CRUD classes.
    """

    @classmethod
    def query(cls, db: Session, **keys) -> Optional[T]:
        ...

    @classmethod
    def read(cls, db: Session, **keys: str) -> S:
        ...

    @classmethod
    def create(cls, db: Session, model: S) -> T:
        ...

    @classmethod
    def update(cls, db: Session, model: S) -> T:
        ...

    @classmethod
    def delete(cls, db: Session, **keys: str):
        ...

    @classmethod
    def db_to_model(cls, db_data_set: T) -> S:
        ...
