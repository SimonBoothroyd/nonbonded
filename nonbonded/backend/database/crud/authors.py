from sqlalchemy.orm import Session

from nonbonded.backend.database import models
from nonbonded.library.models import authors


class AuthorCRUD:

    @staticmethod
    def read_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query(models.Author).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, author: authors.Author) -> models.Author:

        existing_instance = (
            db.query(models.Author)
            .filter(models.Author.name == author.name)
            .filter(models.Author.email == author.email)
            .filter(models.Author.institute == author.institute)
            .first()
        )

        if existing_instance:
            return existing_instance

        db_author = models.Author(**author.dict())

        db.add(db_author)
        db.commit()
        db.refresh(db_author)

        return db_author
