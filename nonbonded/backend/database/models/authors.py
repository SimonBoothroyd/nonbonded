from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Query, Session

from nonbonded.backend.database.models import Base, UniqueMixin


class Author(UniqueMixin, Base):

    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    institute = Column(String, nullable=False)

    @classmethod
    def _hash(cls, db_instance: "Author"):
        return hash((db_instance.name, db_instance.email, db_instance.institute))

    @classmethod
    def _query(cls, db: Session, db_instance: "Author") -> Query:

        return (
            db.query(Author)
            .filter(Author.name == db_instance.name)
            .filter(Author.email == db_instance.email)
            .filter(Author.institute == db_instance.institute)
        )
