"""Fix esp settings constraint.

Revision ID: 62dc1b247022
Revises: f52bb314d86f
Create Date: 2020-09-24 15:35:21.870241

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "62dc1b247022"
down_revision = "f52bb314d86f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "recharge_esp_settings_basis_method_key",
        "recharge_esp_settings",
        type_="unique",
    )
    op.create_unique_constraint(
        None, "recharge_esp_settings", ["basis", "method", "psi4_dft_grid_settings"]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "recharge_esp_settings", type_="unique")
    op.create_unique_constraint(
        "recharge_esp_settings_basis_method_key",
        "recharge_esp_settings",
        ["basis", "method"],
    )
    # ### end Alembic commands ###
