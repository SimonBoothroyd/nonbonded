from sqlalchemy import Column, Integer, String

from nonbonded.backend.database.models import Base


class Author(Base):

    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)
    email = Column(String, unique=True)
    institute = Column(String)
