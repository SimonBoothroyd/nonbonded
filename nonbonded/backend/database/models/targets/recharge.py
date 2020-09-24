from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Query, Session, relationship

from nonbonded.backend.database.models import Base, UniqueMixin
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
        "molecule_set_id",
        String,
        ForeignKey("molecule_sets.id"),
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


class RechargePCMSettings(Base):

    __tablename__ = "recharge_pcm_settings"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("recharge_targets.id"), nullable=False)

    solver = Column(String(6), nullable=False)
    solvent = Column(String(20), nullable=False)

    radii_model = Column(String(8), nullable=False)
    radii_scaling = Column(Boolean, nullable=False)

    cavity_area = Column(Float)


class RechargeESPSettings(Base, UniqueMixin):

    __tablename__ = "recharge_esp_settings"
    __table_args__ = (UniqueConstraint("basis", "method"),)

    id = Column(Integer, primary_key=True, index=True)

    basis = Column(String, nullable=False)
    method = Column(String, nullable=False)

    psi4_dft_grid_settings = Column(String, nullable=False)

    @classmethod
    def _hash(cls, db_instance: "RechargeESPSettings"):
        return hash(
            (db_instance.basis, db_instance.method, db_instance.psi4_dft_grid_settings)
        )

    @classmethod
    def _query(cls, db: Session, db_instance: "RechargeESPSettings") -> Query:
        return (
            db.query(RechargeESPSettings)
            .filter(RechargeESPSettings.basis == db_instance.basis)
            .filter(RechargeESPSettings.method == db_instance.method)
            .filter(
                RechargeESPSettings.psi4_dft_grid_settings
                == db_instance.psi4_dft_grid_settings
            )
        )


class RechargeConformerSettings(Base, UniqueMixin):

    __tablename__ = "recharge_conformer_settings"
    __table_args__ = (UniqueConstraint("method", "sampling_mode", "max_conformers"),)

    id = Column(Integer, primary_key=True, index=True)

    method = Column(String(16), nullable=False)
    sampling_mode = Column(String(8), nullable=False)

    max_conformers = Column(Integer, nullable=False)

    @classmethod
    def _hash(cls, db_instance: "RechargeConformerSettings"):
        return hash(
            (db_instance.method, db_instance.sampling_mode, db_instance.max_conformers)
        )

    @classmethod
    def _query(cls, db: Session, db_instance: "RechargeConformerSettings") -> Query:
        return (
            db.query(RechargeConformerSettings)
            .filter(RechargeConformerSettings.method == db_instance.method)
            .filter(
                RechargeConformerSettings.sampling_mode == db_instance.sampling_mode
            )
            .filter(
                RechargeConformerSettings.max_conformers == db_instance.max_conformers
            )
        )


class RechargeTarget(OptimizationTarget):

    __tablename__ = "recharge_targets"

    id = Column(Integer, ForeignKey("optimization_targets.id"), primary_key=True)

    training_sets = relationship(
        "MoleculeSet",
        secondary=recharge_training_table,
        backref="optimizations",
    )

    grid_settings = relationship(
        "RechargeGridSettings",
        uselist=False,
        cascade="all, delete-orphan",
    )
    pcm_settings = relationship(
        "RechargePCMSettings",
        uselist=False,
        cascade="all, delete-orphan",
    )

    esp_settings = relationship("RechargeESPSettings", uselist=False)
    esp_settings_id = Column(
        Integer, ForeignKey("recharge_esp_settings.id"), nullable=False
    )

    conformer_settings = relationship("RechargeConformerSettings", uselist=False)
    conformer_settings_id = Column(
        Integer, ForeignKey("recharge_conformer_settings.id"), nullable=False
    )

    property = Column(String(14))

    __mapper_args__ = {"polymorphic_identity": "recharge"}
