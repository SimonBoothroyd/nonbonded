from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import Base

author_data_sets_table = Table(
    "author_data_sets",
    Base.metadata,
    Column("dataset_id", String, ForeignKey("data_sets.id")),
    Column("author_id", Integer, ForeignKey("authors.id")),
)


class Component(Base):

    __tablename__ = "component"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("data_set_entries.id"))

    smiles = Column(String)

    mole_fraction = Column(Float)
    exact_amount = Column(Integer)

    role = Column(String)


class DataSetEntry(Base):

    __tablename__ = "data_set_entries"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(String, ForeignKey("data_sets.id"))

    property_type = Column(String)

    temperature = Column(Float)
    pressure = Column(Float)
    phase = Column(String)

    unit = Column(String)

    value = Column(Float)
    std_error = Column(Float)

    doi = Column(String)

    components = relationship("Component", cascade="all, delete-orphan")


class DataSet(Base):

    __tablename__ = "data_sets"

    id = Column(String, primary_key=True, index=True)

    description = Column(String)
    authors = relationship("Author", secondary=author_data_sets_table)

    entries = relationship("DataSetEntry", cascade="all, delete-orphan")

    optimizations = relationship("Optimization", back_populates="training_set")
    benchmarks = relationship("Benchmark", back_populates="test_set")
