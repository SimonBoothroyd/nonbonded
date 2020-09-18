from sqlalchemy import Column, String
from sqlalchemy.orm import Query, Session

from nonbonded.backend.database.models import Base, UniqueMixin


class ChemicalEnvironment(UniqueMixin, Base):

    __tablename__ = "chemical_environments"
    id = Column(String, primary_key=True, index=True, unique=True)

    @classmethod
    def _hash(cls, db_instance: "ChemicalEnvironment"):
        return hash(db_instance.id)

    @classmethod
    def _query(cls, db: Session, db_instance: "ChemicalEnvironment") -> Query:
        return db.query(ChemicalEnvironment).filter(
            ChemicalEnvironment.id == db_instance.id
        )
