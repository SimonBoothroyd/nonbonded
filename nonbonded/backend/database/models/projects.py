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

    study_id = Column(Integer, ForeignKey("studies.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))

    title = Column(String)
    identifier = Column(String, index=True)

    description = Column(String)

    target_training_set = relationship("TargetDataSet")
    target_training_set_id = Column(Integer, ForeignKey("target_data_sets.id"))

    training_set = relationship("DataSet")
    training_set_id = Column(String, ForeignKey("data_sets.id"))

    parameters_to_train = relationship(
        "SmirnoffParameter", secondary=optimization_parameters_table
    )

    # denominators: Dict[str, str]
    # priors: Dict[str, float]


class Study(Base):

    __tablename__ = "studies"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))

    title = Column(String)
    identifier = Column(String, index=True)

    description = Column(String)

    optimizations = relationship("Optimization")
    optimization_inputs = relationship("ForceBalanceOptions", uselist=False)

    target_test_set = relationship("TargetDataSet", uselist=False)
    target_test_set_id = Column(Integer, ForeignKey("target_data_sets.id"))

    test_set = relationship("DataSet")
    test_set_id = Column(String, ForeignKey("data_sets.id"))

    initial_force_field = Column(String)


class Project(Base):

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, unique=True)
    identifier = Column(String, unique=True, index=True)

    abstract = Column(String)

    authors = relationship("Author", secondary=author_projects_table)
    studies = relationship("Study")
