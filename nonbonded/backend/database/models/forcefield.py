from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Query, Session

from nonbonded.backend.database.models import Base, UniqueMixin


class Parameter(UniqueMixin, Base):

    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True, index=True)

    handler_type = Column(String, nullable=False)
    smirks = Column(String, nullable=False)
    attribute_name = Column(String, nullable=False)

    @classmethod
    def _hash(cls, db_instance: "Parameter"):
        return hash(
            (db_instance.handler_type, db_instance.smirks, db_instance.attribute_name)
        )

    @classmethod
    def _query(cls, db: Session, db_instance: "Parameter") -> Query:
        return (
            db.query(Parameter)
            .filter(Parameter.handler_type == db_instance.handler_type)
            .filter(Parameter.smirks == db_instance.smirks)
            .filter(Parameter.attribute_name == db_instance.attribute_name)
        )


class ForceField(UniqueMixin, Base):

    __tablename__ = "force_fields"

    id = Column(Integer, primary_key=True, index=True)
    inner_content = Column(String, nullable=False)

    @classmethod
    def _hash(cls, db_instance: "ForceField"):
        return hash(db_instance.inner_content)

    @classmethod
    def _query(cls, db: Session, db_instance: "ForceField") -> Query:
        return db.query(ForceField).filter(
            ForceField.inner_content == db_instance.inner_content
        )
