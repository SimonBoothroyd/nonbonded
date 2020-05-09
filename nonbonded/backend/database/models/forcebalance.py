from sqlalchemy import Column, Float, ForeignKey, Integer, String

from nonbonded.backend.database.models import Base


class ForceBalanceOptions(Base):

    __tablename__ = "forcebalance"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("studies.id"))

    max_iterations = Column(Integer)

    convergence_step_criteria = Column(Float)
    convergence_objective_criteria = Column(Float)
    convergence_gradient_criteria = Column(Float)

    n_criteria = Column(Integer)

    target_name = Column(String)
