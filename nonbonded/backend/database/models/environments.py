from sqlalchemy import Column, Integer, String

from nonbonded.backend.database.models import Base


class ChemicalEnvironment(Base):

    __tablename__ = "chemical_environments"

    id = Column(Integer, primary_key=True, index=True)
    value = Column(String, unique=True)
