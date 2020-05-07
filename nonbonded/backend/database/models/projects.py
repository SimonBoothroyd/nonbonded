from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import (
    Base,
    ForceBalanceOptions,
    SmirnoffParameter,
)
from nonbonded.library.models import projects

author_projects_table = Table(
    "author_projects",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id")),
    Column("author_id", Integer, ForeignKey("authors.id")),
)


class Author(Base):

    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)
    email = Column(String, unique=True)
    institute = Column(String)

    @classmethod
    def from_schema(cls, schema: projects.Author):

        # noinspection PyArgumentList
        return cls(**schema.dict())


class Optimization(Base):

    __tablename__ = "optimizations"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("studies.id"))

    title = Column(String, unique=True)
    identifier = Column(String)

    description = Column(String)

    # target_training_set: TargetDataSet
    parameters_to_train = relationship("SmirnoffParameter")

    # denominators: Dict[str, str]
    # priors: Dict[str, float]

    @classmethod
    def from_schema(cls, schema: projects.Optimization):

        # noinspection PyArgumentList
        return cls(
            title=schema.title,
            identifier=schema.identifier,
            description=schema.description,
            parameters_to_train=[
                SmirnoffParameter.from_schema(x) for x in schema.parameters_to_train
            ],
        )


class Study(Base):

    __tablename__ = "studies"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("projects.id"))

    title = Column(String, unique=True)
    identifier = Column(String)

    description = Column(String)

    optimizations = relationship("Optimization")
    optimization_inputs = relationship("ForceBalanceOptions", uselist=False)

    # target_test_set: TargetDataSet

    initial_force_field = Column(String)

    @classmethod
    def from_schema(cls, schema: projects.Study):

        # noinspection PyArgumentList
        return cls(
            title=schema.title,
            identifier=schema.identifier,
            description=schema.description,
            optimizations=[Optimization.from_schema(x) for x in schema.optimizations],
            optimization_inputs=ForceBalanceOptions.from_schema(
                schema.optimization_inputs
            ),
        )


class Project(Base):

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, unique=True)
    identifier = Column(String, unique=True, index=True)

    abstract = Column(String)

    authors = relationship("Author", secondary=author_projects_table)
    studies = relationship("Study")

    @classmethod
    def from_schema(cls, schema: projects.Project):

        # noinspection PyArgumentList
        return cls(
            title=schema.title,
            identifier=schema.identifier,
            abstract=schema.abstract,
            authors=[Author.from_schema(x) for x in schema.authors],
            studies=[Study.from_schema(x) for x in schema.studies],
        )
