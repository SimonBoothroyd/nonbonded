from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import Base
from nonbonded.backend.database.models.targets import OptimizationTarget

recharge_training_table = Table(
    "recharge_training_sets",
    Base.metadata,
    Column(
        "recharge_targets",
        Integer,
        ForeignKey("recharge_targets.id"),
        primary_key=True,
    ),
    Column(
        "qc_data_set_id",
        String,
        ForeignKey("qc_data_sets.id"),
        primary_key=True,
    ),
)


class RechargeGridSettings(Base):

    __tablename__ = "recharge_grid_settings"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("recharge_targets.id"), nullable=False)

    type = Column(String(32), nullable=False)
    spacing = Column(Float, nullable=False)

    inner_vdw_scale = Column(Float, nullable=False)
    outer_vdw_scale = Column(Float, nullable=False)


class RechargeTarget(OptimizationTarget):

    __tablename__ = "recharge_targets"

    id = Column(Integer, ForeignKey("optimization_targets.id"), primary_key=True)

    training_sets = relationship(
        "QCDataSet",
        secondary=recharge_training_table,
        backref="optimizations",
    )

    grid_settings = relationship(
        "RechargeGridSettings",
        uselist=False,
        cascade="all, delete-orphan",
    )

    property = Column(String(14))

    __mapper_args__ = {"polymorphic_identity": "recharge"}
