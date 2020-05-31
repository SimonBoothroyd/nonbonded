from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import Base


class BaseStatisticsEntry(Base):

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

    statistics_type = Column(String)

    property_type = Column(String)
    n_components = Column(Integer)

    category = Column(String)

    value = Column(Float)

    lower_95_ci = Column(Float)
    upper_95_ci = Column(Float)


class BenchmarkResultsEntry(Base):

    __tablename__ = "benchmark_results_entries"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("benchmark_results.id"), nullable=False)

    reference_id = Column(Integer, ForeignKey("data_set_entries.id"), nullable=False)

    estimated_value = Column(Float)
    estimated_std_error = Column(Float)

    category = Column(String)


class BenchmarkStatisticsEntry(BaseStatisticsEntry):

    __tablename__ = "benchmark_statistics_entries"
    parent_id = Column(Integer, ForeignKey("benchmark_results.id"), nullable=False)


class BenchmarkResult(Base):

    __tablename__ = "benchmark_results"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("benchmarks.id"), nullable=False)
    parent = relationship("Benchmark", back_populates="results")

    results_entries = relationship(
        "BenchmarkResultsEntry", cascade="all, delete-orphan"
    )
    statistic_entries = relationship(
        "BenchmarkStatisticsEntry", cascade="all, delete-orphan"
    )


class ObjectiveFunction(Base):

    __tablename__ = "objective_function"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("optimization_results.id"))

    iteration = Column(Integer)
    value = Column(Float)


class RefitForceField(Base):

    __tablename__ = "refit_force_fields"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("optimization_results.id"), nullable=False)
    parent = relationship(
        "OptimizationResult", back_populates="refit_force_field", uselist=False
    )

    inner_xml = Column(String)


class OptimizationStatisticsEntry(BaseStatisticsEntry):

    __tablename__ = "optimization_statistics_entries"

    parent_id = Column(Integer, ForeignKey("optimization_results.id"), nullable=False)
    iteration = Column(Integer)


class OptimizationResult(Base):

    __tablename__ = "optimization_results"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("optimizations.id"), nullable=False)
    parent = relationship("Optimization", back_populates="results")

    objective_function = relationship(
        "ObjectiveFunction", cascade="all, delete-orphan", lazy="joined"
    )
    statistics = relationship(
        "OptimizationStatisticsEntry", cascade="all, delete-orphan", lazy="joined"
    )

    refit_force_field = relationship(
        "RefitForceField",
        back_populates="parent",
        cascade="all, delete-orphan",
        uselist=False,
    )
