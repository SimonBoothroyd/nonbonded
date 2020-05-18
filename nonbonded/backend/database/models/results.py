from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import Base


class ResultsComponent(Base):

    __tablename__ = "results_components"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("data_set_entries.id"))

    smiles = Column(String)

    mole_fraction = Column(Float)
    exact_amount = Column(Integer)

    role = Column(String)


class ResultsEntry(Base):

    __tablename__ = "results_entries"

    id = Column(Integer, primary_key=True, index=True)

    property_type = Column(String)

    temperature = Column(Float)
    pressure = Column(Float)
    phase = Column(String)

    components = relationship("ResultsComponent", cascade="all, delete-orphan")

    unit = Column(String)

    reference_value = Column(Float)
    reference_std_error = Column(Float)

    estimated_value = Column(Float)
    estimated_std_error = Column(Float)

    category = Column(String)


class StatisticsEntry(Base):

    __tablename__ = "statistics_entries"

    id = Column(Integer, primary_key=True, index=True)

    statistics_type = Column(String)

    property_type = Column(String)
    n_components = Column(Integer)

    category = Column(String)

    unit = Column(String)

    value = Column(Float)

    lower_95_ci = Column(Float)
    upper_95_ci = Column(Float)


class BenchmarkResult(Base):

    __tablename__ = "benchmark_results"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("benchmarks.id"), nullable=False)
    parent = relationship("Benchmark", back_populates="results", nullable=False)

    statistic_entries_id = Column(Integer, ForeignKey("statistics_entries.id"))
    statistic_entries = relationship("StatisticsEntry", cascade="all, delete-orphan")

    result_entries_id = Column(Integer, ForeignKey("results_entries.id"))
    results_entries = relationship("ResultsEntry", cascade="all, delete-orphan")


class ObjectiveFunction(Base):

    __tablename__ = "objective_function"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("optimization_results.id"))

    iteration = Column(Integer)
    value = Column(Float)


class OptimizationResult(Base):

    __tablename__ = "optimization_results"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("optimizations.id"), nullable=False)
    parent = relationship("Optimization", back_populates="results", nullable=False)

    objective_function = relationship("ObjectiveFunction", cascade="all, delete-orphan")

    refit_force_field_id = Column(Integer, ForeignKey("refit_force_fields.id"))
    refit_force_field = relationship(
        "RefitForceField", back_populates="parent", cascade="all, delete-orphan"
    )
