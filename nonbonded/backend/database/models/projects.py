from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import backref, relationship
from sqlalchemy_utils import auto_delete_orphans

from nonbonded.backend.database.models import Base

author_projects_table = Table(
    "author_projects",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)

sub_study_environment_table = Table(
    "sub_study_environments",
    Base.metadata,
    Column("sub_study_id", Integer, ForeignKey("sub_studies.id"), primary_key=True),
    Column(
        "environment_id",
        String,
        ForeignKey("chemical_environments.id"),
        primary_key=True,
    ),
)
sub_study_force_field_table = Table(
    "sub_study_force_fields",
    Base.metadata,
    Column("sub_study_id", Integer, ForeignKey("sub_studies.id"), primary_key=True),
    Column("force_field_id", Integer, ForeignKey("force_fields.id"), primary_key=True),
)

optimization_parameters_table = Table(
    "optimization_parameters",
    Base.metadata,
    Column(
        "optimization_id", Integer, ForeignKey("optimizations.id"), primary_key=True
    ),
    Column("parameter_id", Integer, ForeignKey("parameters.id"), primary_key=True),
)

benchmark_test_sets_table = Table(
    "benchmark_test_sets",
    Base.metadata,
    Column("benchmark_id", Integer, ForeignKey("benchmarks.id"), primary_key=True),
    Column(
        "data_set_id",
        String,
        ForeignKey("data_sets.id"),
        primary_key=True,
    ),
)


class SubStudy(Base):
    """A base class for optimization and benchmark sub-studies, which share largely the
    same fields.
    """

    __tablename__ = "sub_studies"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(12))

    identifier = Column(String(32), index=True, nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    force_field = relationship(
        "ForceField",
        secondary=sub_study_force_field_table,
        backref="sub_studies",
        uselist=False,
    )

    optimization_id = Column(Integer, ForeignKey("sub_studies.id"))
    children = relationship(
        "SubStudy", backref=backref("optimization", remote_side=[id])
    )

    analysis_environments = relationship(
        "ChemicalEnvironment", secondary=sub_study_environment_table
    )

    __mapper_args__ = {"polymorphic_on": type}


class Optimization(SubStudy):

    __tablename__ = "optimizations"

    id = Column(Integer, ForeignKey("sub_studies.id"), primary_key=True)

    parent_id = Column(Integer, ForeignKey("studies.id"), nullable=False)
    parent = relationship("Study", back_populates="optimizations")

    force_balance_engine = relationship(
        "ForceBalance", uselist=False, cascade="all, delete-orphan"
    )

    evaluator_targets = relationship("EvaluatorTarget", cascade="all, delete-orphan")
    recharge_targets = relationship("RechargeTarget", cascade="all, delete-orphan")

    max_iterations = Column(Integer, nullable=False)

    parameters_to_train = relationship(
        "Parameter", secondary=optimization_parameters_table, backref="optimizations"
    )

    results = relationship("OptimizationResult", uselist=False, back_populates="parent")

    __mapper_args__ = {"polymorphic_identity": "optimization"}


class Benchmark(SubStudy):

    __tablename__ = "benchmarks"

    id = Column(Integer, ForeignKey("sub_studies.id"), primary_key=True)

    parent_id = Column(Integer, ForeignKey("studies.id"), nullable=False)
    parent = relationship("Study", back_populates="benchmarks")

    test_sets = relationship(
        "DataSet",
        secondary=benchmark_test_sets_table,
        backref="benchmarks",
    )

    results = relationship("BenchmarkResult", uselist=False, back_populates="parent")

    __mapper_args__ = {"polymorphic_identity": "benchmark"}


class Study(Base):

    __tablename__ = "studies"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    parent = relationship("Project", back_populates="studies")

    identifier = Column(String, index=True, nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    optimizations = relationship("Optimization", back_populates="parent")
    benchmarks = relationship("Benchmark", back_populates="parent")


class Project(Base):

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, unique=True, index=True, nullable=False)

    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)

    authors = relationship("Author", secondary=author_projects_table)
    studies = relationship("Study", back_populates="parent")


auto_delete_orphans(Optimization.parameters_to_train)
