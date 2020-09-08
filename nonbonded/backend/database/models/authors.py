from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Query

from nonbonded.backend.database.models import Base, UniqueMixin


class Author(UniqueMixin, Base):

    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    institute = Column(String, nullable=False)

    @classmethod
    def unique_hash(cls, name, email, institute):
        return name, email, institute

    @classmethod
    def unique_filter(cls, query: Query, name, email, institute):
        return (
            query.filter(Author.name == name)
            .filter(Author.email == email)
            .filter(Author.institute == institute)
        )
