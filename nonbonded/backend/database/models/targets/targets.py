from sqlalchemy import Column, Float, ForeignKey, Integer, String

from nonbonded.backend.database.models import Base


class OptimizationTarget(Base):

    __tablename__ = "optimization_targets"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(10))

    parent_id = Column(Integer, ForeignKey("optimizations.id"), nullable=False)

    identifier = Column(String(32), nullable=False)
    weight = Column(Float, nullable=False)

    __mapper_args__ = {"polymorphic_on": type}
