from sqlalchemy import Column, String
from sqlalchemy.orm import Query

from nonbonded.backend.database.models import Base, UniqueMixin


class ChemicalEnvironment(UniqueMixin, Base):

    __tablename__ = "chemical_environments"
    id = Column(String, primary_key=True, index=True, unique=True)

    @classmethod
    def unique_hash(cls, identifier):
        return identifier

    @classmethod
    def unique_filter(cls, query: Query, identifier):
        return query.filter(ChemicalEnvironment.id == identifier)
