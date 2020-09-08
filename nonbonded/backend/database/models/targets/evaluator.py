from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import Base
from nonbonded.backend.database.models.targets import OptimizationTarget

evaluator_training_table = Table(
    "evaluator_training_sets",
    Base.metadata,
    Column(
        "evaluator_targets",
        Integer,
        ForeignKey("evaluator_targets.id"),
        primary_key=True,
    ),
    Column("data_set_id", String, ForeignKey("data_sets.id"), primary_key=True),
)


class EvaluatorDenominator(Base):

    __tablename__ = "evaluator_denominators"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("evaluator_targets.id"))

    property_type = Column(String, nullable=False)
    value = Column(String, nullable=False)


class EvaluatorTarget(OptimizationTarget):

    __tablename__ = "evaluator_targets"

    id = Column(Integer, ForeignKey("optimization_targets.id"), primary_key=True)

    training_sets = relationship(
        "DataSet",
        secondary=evaluator_training_table,
        backref="optimizations",
    )
    denominators = relationship("EvaluatorDenominator", cascade="all, delete-orphan")

    allow_direct_simulation = Column(Boolean, nullable=False)
    n_molecules = Column(Integer)

    allow_reweighting = Column(Boolean, nullable=False)
    n_effective_samples = Column(Integer)

    __mapper_args__ = {"polymorphic_identity": "evaluator"}
