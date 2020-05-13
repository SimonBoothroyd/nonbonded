from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import Base

target_data_environment_table = Table(
    "target_data_environment",
    Base.metadata,
    Column("target_data_set_id", Integer, ForeignKey("target_data_sets.id")),
    Column("environment_id", Integer, ForeignKey("chemical_environments.id")),
)
author_data_sets_table = Table(
    "author_data_sets",
    Base.metadata,
    Column("dataset_id", String, ForeignKey("data_sets.id")),
    Column("author_id", Integer, ForeignKey("authors.id")),
)


class TargetAmount(Base):

    __tablename__ = "target_amounts"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("target_properties.id"))

    mole_fraction = Column(Float)


class TargetEnvironment(Base):

    __tablename__ = "target_environments"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("target_data_sets.id"))

    value = Column(String)


class TargetProperty(Base):

    __tablename__ = "target_properties"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("target_data_sets.id"))

    property_type = Column(String)

    temperature = Column(Float)
    pressure = Column(Float)

    n_components = Column(Integer)

    mole_fractions = relationship("TargetAmount")


class TargetDataSet(Base):

    __tablename__ = "target_data_sets"

    id = Column(Integer, primary_key=True, index=True)

    target_properties = relationship("TargetProperty")
    chemical_environments = relationship(
        "ChemicalEnvironment", secondary=target_data_environment_table
    )


class ComponentAmount(Base):

    __tablename__ = "component_amounts"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("data_set_entries.id"))

    smiles = Column(String)
    mole_fraction = Column(Float)


class DataSetEntry(Base):

    __tablename__ = "data_set_entries"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("data_sets.id"))

    property_type = Column(String)

    temperature = Column(Float)
    pressure = Column(Float)

    value = Column(Float)
    std_error = Column(Float)

    doi = Column(String)

    components = relationship("ComponentAmount")


class DataSet(Base):

    __tablename__ = "data_sets"

    id = Column(String, primary_key=True, index=True)

    description = Column(String)
    authors = relationship("Author", secondary=author_data_sets_table)

    entries = relationship("DataSetEntry")
