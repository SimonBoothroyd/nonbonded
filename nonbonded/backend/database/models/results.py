from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import Base

results_force_field_table = Table(
    "results_force_fields",
    Base.metadata,
    Column(
        "results_id", Integer, ForeignKey("optimization_results.id"), primary_key=True
    ),
    Column("force_field_id", Integer, ForeignKey("force_fields.id"), primary_key=True),
)


class Statistic(Base):

    __tablename__ = "statistics"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(12))

    statistic_type = Column(String)

    value = Column(Float)

    lower_95_ci = Column(Float)
    upper_95_ci = Column(Float)

    category = Column(String)

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "base"}


class DataSetStatistic(Statistic):

    __tablename__ = "data_set_statistics"

    id = Column(Integer, ForeignKey("statistics.id"), primary_key=True)
    parent_id = Column(Integer, ForeignKey("data_set_results.id"), nullable=False)

    property_type = Column(String)
    n_components = Column(Integer)

    __mapper_args__ = {"polymorphic_identity": "data-set"}


class DataSetResultEntry(Base):

    __tablename__ = "data_set_result_entries"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("data_set_results.id"), nullable=False)

    reference_id = Column(Integer, ForeignKey("data_set_entries.id"), nullable=False)
    reference = relationship("DataSetEntry", uselist=False)

    estimated_value = Column(Float)
    estimated_std_error = Column(Float)

    category = Column(String)


class DataSetResult(Base):

    __tablename__ = "data_set_results"

    id = Column(Integer, primary_key=True, index=True)

    result_entries = relationship("DataSetResultEntry", cascade="all, delete-orphan")
    statistic_entries = relationship("DataSetStatistic", cascade="all, delete-orphan")


class MoleculeSetStatistic(Statistic):

    __tablename__ = "molecule_set_statistics"

    id = Column(Integer, ForeignKey("statistics.id"), primary_key=True)
    parent_id = Column(Integer, ForeignKey("molecule_set_results.id"), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "molecule-set"}


class MoleculeSetResult(Base):

    __tablename__ = "molecule_set_results"

    id = Column(Integer, primary_key=True, index=True)

    statistic_entries = relationship(
        "MoleculeSetStatistic", cascade="all, delete-orphan"
    )


class BenchmarkResult(Base):

    __tablename__ = "benchmark_results"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("benchmarks.id"), nullable=False)
    parent = relationship("Benchmark", back_populates="results")

    data_set_result_id = Column(Integer, ForeignKey("data_set_results.id"))
    data_set_result = relationship(
        "DataSetResult", uselist=False, cascade="all, delete-orphan", single_parent=True
    )


class TargetResult(Base):

    __tablename__ = "target_results"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(10))

    parent_id = Column(Integer, ForeignKey("optimization_results.id"), nullable=False)

    target_id = Column(Integer, ForeignKey("optimization_targets.id"), nullable=False)
    target = relationship("OptimizationTarget")

    iteration = Column(Integer, nullable=False)
    objective_function = Column(Float, nullable=False)

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "target"}


class EvaluatorTargetResult(TargetResult):

    __tablename__ = "evaluator_target_results"

    id = Column(Integer, ForeignKey("target_results.id"), primary_key=True)

    data_set_result_id = Column(Integer, ForeignKey("data_set_results.id"))
    data_set_result = relationship(
        "DataSetResult", uselist=False, cascade="all, delete-orphan", single_parent=True
    )

    __mapper_args__ = {"polymorphic_identity": "evaluator"}


class RechargeTargetResult(TargetResult):
    __tablename__ = "recharge_target_results"

    id = Column(Integer, ForeignKey("target_results.id"), primary_key=True)

    molecule_set_result_id = Column(Integer, ForeignKey("molecule_set_results.id"))
    molecule_set_result = relationship(
        "MoleculeSetResult",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )

    __mapper_args__ = {"polymorphic_identity": "recharge"}


class OptimizationResult(Base):

    __tablename__ = "optimization_results"

    id = Column(Integer, primary_key=True, index=True)

    parent_id = Column(Integer, ForeignKey("optimizations.id"), nullable=False)
    parent = relationship("Optimization", back_populates="results")

    evaluator_target_results = relationship(
        "EvaluatorTargetResult", cascade="all, delete-orphan"
    )
    recharge_target_results = relationship(
        "RechargeTargetResult", cascade="all, delete-orphan"
    )

    refit_force_field = relationship(
        "ForceField",
        secondary=results_force_field_table,
        backref="results",
        uselist=False,
    )
