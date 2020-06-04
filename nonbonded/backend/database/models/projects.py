from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Query, relationship
from sqlalchemy_utils import auto_delete_orphans

from nonbonded.backend.database.models import Base, UniqueMixin

author_projects_table = Table(
    "author_projects",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)

optimization_environment_table = Table(
    "optimization_environments",
    Base.metadata,
    Column(
        "optimization_id",
        Integer,
        ForeignKey("optimizations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "environment_id",
        String,
        ForeignKey("chemical_environments.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
benchmark_environment_table = Table(
    "benchmark_environments",
    Base.metadata,
    Column(
        "benchmark_id",
        Integer,
        ForeignKey("benchmarks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "environment_id",
        String,
        ForeignKey("chemical_environments.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

optimization_parameters_table = Table(
    "optimization_parameters",
    Base.metadata,
    Column(
        "optimization_id",
        Integer,
        ForeignKey("optimizations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "parameter_id",
        Integer,
        ForeignKey("parameters.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

optimization_force_field_table = Table(
    "optimization_force_fields",
    Base.metadata,
    Column(
        "optimization_id",
        Integer,
        ForeignKey("optimizations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "force_field_id",
        Integer,
        ForeignKey("initial_force_fields.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

optimization_training_table = Table(
    "optimization_training_sets",
    Base.metadata,
    Column(
        "optimization_id",
        Integer,
        ForeignKey("optimizations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "data_set_id",
        String,
        ForeignKey("data_sets.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)

benchmark_test_table = Table(
    "benchmark_test_sets",
    Base.metadata,
    Column(
        "benchmark_id",
        Integer,
        ForeignKey("benchmarks.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "data_set_id",
        String,
        ForeignKey("data_sets.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)


class Denominator(Base):

    __tablename__ = "denominators"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("optimizations.id"))

    property_type = Column(String)
    value = Column(String)


class Prior(Base):

    __tablename__ = "priors"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("optimizations.id"))

    parameter_type = Column(String)
    value = Column(Float)


class InitialForceField(UniqueMixin, Base):

    __tablename__ = "initial_force_fields"

    id = Column(Integer, primary_key=True, index=True)
    inner_xml = Column(String)

    @classmethod
    def unique_hash(cls, inner_xml):
        return inner_xml

    @classmethod
    def unique_filter(cls, query: Query, inner_xml):
        return query.filter(InitialForceField.inner_xml == inner_xml)


class Optimization(Base):

    __tablename__ = "optimizations"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("studies.id"), nullable=False)
    parent = relationship("Study", back_populates="optimizations")

    identifier = Column(String, index=True)

    name = Column(String)
    description = Column(String)

    training_sets = relationship(
        "DataSet", secondary=optimization_training_table, backref="optimizations",
    )

    initial_force_field = relationship(
        "InitialForceField",
        secondary=optimization_force_field_table,
        backref="optimizations",
        uselist=False,
    )

    parameters_to_train = relationship(
        "Parameter", secondary=optimization_parameters_table, backref="optimizations"
    )
    force_balance_input = relationship(
        "ForceBalanceOptions", uselist=False, cascade="all, delete-orphan"
    )

    denominators = relationship("Denominator", cascade="all, delete-orphan")
    priors = relationship("Prior", cascade="all, delete-orphan")

    analysis_environments = relationship(
        "ChemicalEnvironment", secondary=optimization_environment_table
    )

    results = relationship("OptimizationResult", uselist=False, back_populates="parent")


class Benchmark(Base):

    __tablename__ = "benchmarks"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("studies.id"), nullable=False)
    parent = relationship("Study", back_populates="benchmarks")

    identifier = Column(String, index=True)

    name = Column(String)
    description = Column(String)

    test_sets = relationship(
        "DataSet", secondary=benchmark_test_table, backref="benchmarks",
    )

    optimization_id = Column(Integer, ForeignKey("optimizations.id"))
    optimization = relationship("Optimization", backref="benchmarks")

    force_field_name = Column(String)

    analysis_environments = relationship(
        "ChemicalEnvironment", secondary=benchmark_environment_table
    )

    results = relationship("BenchmarkResult", uselist=False, back_populates="parent")


class Study(Base):

    __tablename__ = "studies"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    parent = relationship("Project", back_populates="studies")

    identifier = Column(String, index=True)

    name = Column(String)
    description = Column(String)

    optimizations = relationship(
        "Optimization", back_populates="parent", cascade="all, delete-orphan"
    )
    benchmarks = relationship(
        "Benchmark", back_populates="parent", cascade="all, delete-orphan"
    )


class Project(Base):

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, unique=True, index=True)

    name = Column(String, unique=True)
    description = Column(String)

    authors = relationship("Author", secondary=author_projects_table)
    studies = relationship(
        "Study", back_populates="parent", cascade="all, delete-orphan"
    )


auto_delete_orphans(Optimization.initial_force_field)
auto_delete_orphans(Optimization.parameters_to_train)
