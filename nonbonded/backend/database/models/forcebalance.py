from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from nonbonded.backend.database.models import Base


class ForceBalanceOptions(Base):

    __tablename__ = "forcebalance"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("optimizations.id"))

    max_iterations = Column(Integer)

    convergence_step_criteria = Column(Float)
    convergence_objective_criteria = Column(Float)
    convergence_gradient_criteria = Column(Float)

    n_criteria = Column(Integer)

    initial_trust_radius = Column(Float)
    minimum_trust_radius = Column(Float)

    evaluator_target_name = Column(String)

    allow_direct_simulation = Column(Boolean)
    n_molecules = Column(Integer)

    allow_reweighting = Column(Boolean)
    n_effective_samples = Column(Integer)
