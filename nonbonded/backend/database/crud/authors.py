from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models import authors


class AuthorCRUD:
    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Author).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, author: authors.Author) -> models.Author:

        db_author = models.Author.unique(db, models.Author(**author.dict()))
        return db_author
