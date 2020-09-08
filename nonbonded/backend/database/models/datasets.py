from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import Base

author_base_sets_table = Table(
    "author_base_sets",
    Base.metadata,
    Column("base_set_id", String(32), ForeignKey("base_sets.id")),
    Column("author_id", Integer, ForeignKey("authors.id")),
)


class BaseSet(Base):
    """A base class for sets of experimental measurements or molecules to train and
    test against."""

    __tablename__ = "base_sets"

    id = Column(String(32), primary_key=True, index=True)
    type = Column(String(12))

    description = Column(String, nullable=False)
    authors = relationship("Author", secondary=author_base_sets_table)

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "base_set"}


class Molecule(Base):

    __tablename__ = "molecules"

    smiles = Column(String, nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(String, ForeignKey("molecule_sets.id"))


class Component(Base):

    __tablename__ = "component"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("data_set_entries.id"), nullable=False)

    smiles = Column(String, nullable=False)

    mole_fraction = Column(Float)
    exact_amount = Column(Integer)

    role = Column(String, nullable=False)


class DataSetEntry(Base):

    __tablename__ = "data_set_entries"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    parent_id = Column(String, ForeignKey("data_sets.id"))

    property_type = Column(String, nullable=False)

    temperature = Column(Float, nullable=False)
    pressure = Column(Float)
    phase = Column(String, nullable=False)

    value = Column(Float, nullable=False)
    std_error = Column(Float)

    doi = Column(String, nullable=False)

    components = relationship("Component", cascade="all, delete-orphan", lazy="joined")


class DataSet(BaseSet):

    __tablename__ = "data_sets"

    id = Column(String(32), ForeignKey("base_sets.id"), primary_key=True)
    entries = relationship("DataSetEntry", cascade="all, delete-orphan", lazy="joined")

    __mapper_args__ = {"polymorphic_identity": "data_set"}


class MoleculeSet(BaseSet):

    __tablename__ = "molecule_sets"

    id = Column(String(32), ForeignKey("base_sets.id"), primary_key=True)
    entries = relationship("Molecule", cascade="all, delete-orphan", lazy="joined")

    __mapper_args__ = {"polymorphic_identity": "molecule_set"}
