from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import Query, relationship

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


class RefitForceField(Base):

    __tablename__ = "refit_force_fields"

    id = Column(Integer, primary_key=True, index=True)
    inner_xml = Column(String, index=True, unique=True)

    parent = relationship(
        "OptimizationResult", back_populates="refit_force_field", uselist=False
    )
