from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from nonbonded.backend.database.models import Base


class ForceBalancePrior(Base):

    __tablename__ = "force_balance_priors"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("force_balance.id"))

    parameter_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)


class ForceBalance(Base):

    __tablename__ = "force_balance"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("optimizations.id"), nullable=False)

    priors = relationship("ForceBalancePrior", cascade="all, delete-orphan")

    convergence_step_criteria = Column(Float, nullable=False)
    convergence_objective_criteria = Column(Float, nullable=False)
    convergence_gradient_criteria = Column(Float, nullable=False)

    n_criteria = Column(Integer, nullable=False)

    initial_trust_radius = Column(Float, nullable=False)
    minimum_trust_radius = Column(Float, nullable=False)
