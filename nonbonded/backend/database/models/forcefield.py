from sqlalchemy import Column, Integer, String

from nonbonded.backend.database.models import Base


class SmirnoffParameter(Base):

    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True, index=True)

    handler_type = Column(String)
    smirks = Column(String)
    attribute_name = Column(String)
