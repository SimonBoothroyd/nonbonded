from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import Base


class ComparisonData(Base):

    __tablename__ = "comparison_data"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("benchmark_results.id"))

    property_type = Column(String)
    n_components = Column(Integer)

    force_field_name = Column(String)

    name = Column(String)

    x = Column(Float)
    y = Column(Float)

    meta_data = Column(String)


class StatisticData(Base):

    __tablename__ = "statistic_data"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("benchmark_results.id"))

    property_type = Column(String)
    n_components = Column(Integer)

    force_field_name = Column(String)
    statistic_type = Column(String)

    value = Column(Float)

    lower_ci = Column(Float)
    upper_ci = Column(Float)


class BenchmarkResults(Base):

    __tablename__ = "benchmark_results"

    __table_args__ = (UniqueConstraint("project_identifier", "study_identifier"),)

    id = Column(Integer, primary_key=True, index=True)

    project_identifier = Column(String)
    study_identifier = Column(String)

    comparison_data = relationship("ComparisonData")
    statistic_data = relationship("StatisticData")


class ObjectiveFunctionData(Base):

    __tablename__ = "objective_function_data"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("optimization_result.id"))

    iteration = Column(Integer)
    value = Column(Float)


class OptimizationResult(Base):

    __tablename__ = "optimization_result"

    __table_args__ = (
        UniqueConstraint(
            "project_identifier", "study_identifier", "optimization_identifier"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    project_identifier = Column(String)
    study_identifier = Column(String)
    optimization_identifier = Column(String)

    objective_function = relationship("ObjectiveFunctionData")
