"""Expose default evaluator options for forcebalance.

Revision ID: 76f4d5475fb1
Revises: d4a84f539879
Create Date: 2020-06-18 15:40:34.583401

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "76f4d5475fb1"
down_revision = "d4a84f539879"
branch_labels = None
depends_on = None


def upgrade():

    op.alter_column(
        "forcebalance",
        column_name="target_name",
        new_column_name="evaluator_target_name",
    )

    op.add_column(
        "forcebalance", sa.Column("allow_reweighting", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "forcebalance", sa.Column("n_effective_samples", sa.Integer(), nullable=True)
    )

    op.add_column(
        "forcebalance",
        sa.Column("allow_direct_simulation", sa.Boolean(), nullable=True),
    )
    op.add_column("forcebalance", sa.Column("n_molecules", sa.Integer(), nullable=True))

    op.add_column(
        "forcebalance", sa.Column("initial_trust_radius", sa.Float(), nullable=True)
    )
    op.add_column(
        "forcebalance", sa.Column("minimum_trust_radius", sa.Float(), nullable=True)
    )

    op.execute("UPDATE forcebalance SET allow_reweighting = false")
    op.execute("UPDATE forcebalance SET allow_direct_simulation = true")

    op.execute("UPDATE forcebalance SET initial_trust_radius = 0.25")
    op.execute("UPDATE forcebalance SET minimum_trust_radius = 0.05")


def downgrade():

    op.drop_column("forcebalance", "minimum_trust_radius")
    op.drop_column("forcebalance", "initial_trust_radius")

    op.drop_column("forcebalance", "n_molecules")
    op.drop_column("forcebalance", "allow_direct_simulation")

    op.drop_column("forcebalance", "n_effective_samples")
    op.drop_column("forcebalance", "allow_reweighting")

    op.alter_column(
        "forcebalance",
        column_name="evaluator_target_name",
        new_column_name="target_name",
    )
