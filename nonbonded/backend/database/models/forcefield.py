from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Query

from nonbonded.backend.database.models import Base, UniqueMixin


class Parameter(UniqueMixin, Base):

    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True, index=True)

    handler_type = Column(String)
    smirks = Column(String)
    attribute_name = Column(String)

    @classmethod
    def unique_hash(cls, handler_type, smirks, attribute_name):
        return handler_type, smirks, attribute_name

    @classmethod
    def unique_filter(cls, query: Query, handler_type, smirks, attribute_name):
        return (
            query.filter(Parameter.handler_type == handler_type)
            .filter(Parameter.smirks == smirks)
            .filter(Parameter.attribute_name == attribute_name)
        )