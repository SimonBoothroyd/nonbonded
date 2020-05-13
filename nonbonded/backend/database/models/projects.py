from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import Base

author_projects_table = Table(
    "author_projects",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id")),
    Column("author_id", Integer, ForeignKey("authors.id")),
)
optimization_parameters_table = Table(
    "optimization_parameters",
    Base.metadata,
    Column("optimization_id", Integer, ForeignKey("optimizations.id")),
    Column("parameter_id", Integer, ForeignKey("parameters.id")),
)


class Optimization(Base):

    __tablename__ = "optimizations"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey('studies.id'))
    parent = relationship("Study", back_populates="optimizations")

    identifier = Column(String, index=True)

    name = Column(String)
    description = Column(String)

    training_set = relationship("DataSet")
    training_set_id = Column(String, ForeignKey("data_sets.id"))

    initial_force_field = Column(String)

    parameters_to_train = relationship(
        "SmirnoffParameter", secondary=optimization_parameters_table
    )
    force_balance_input = relationship("ForceBalanceOptions", uselist=False)

    # denominators: Dict[str, str]
    # priors: Dict[str, float]


class Benchmark(Base):

    __tablename__ = "benchmarks"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey('studies.id'))
    parent = relationship("Study", back_populates="benchmarks")

    identifier = Column(String, index=True)

    name = Column(String)
    description = Column(String)

    test_set = relationship("DataSet")
    test_set_id = Column(String, ForeignKey("data_sets.id"))

    optimization_id = Column(String)

    force_field_name = Column(String)


class Study(Base):

    __tablename__ = "studies"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey('projects.id'))
    parent = relationship("Project", back_populates="studies")

    identifier = Column(String, index=True)

    name = Column(String)
    description = Column(String)

    optimizations = relationship("Optimization", back_populates="parent")
    benchmarks = relationship("Benchmark", back_populates="parent")


class Project(Base):

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, unique=True, index=True)

    name = Column(String, unique=True)
    description = Column(String)

    authors = relationship("Author", secondary=author_projects_table)
    studies = relationship("Study", back_populates="parent")
