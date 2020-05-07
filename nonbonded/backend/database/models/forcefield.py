from sqlalchemy import Column, ForeignKey, Integer, String

from nonbonded.backend.database.models import Base
from nonbonded.library.models import forcefield


class SmirnoffParameter(Base):

    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("optimizations.id"))

    handler_type = Column(String)
    smirks = Column(String)
    attribute_name = Column(String)

    @classmethod
    def from_schema(cls, schema: forcefield.SmirnoffParameter):

        # noinspection PyArgumentList
        return cls(**schema.dict())
