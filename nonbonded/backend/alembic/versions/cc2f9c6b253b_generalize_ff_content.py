"""Generalize FF content

Revision ID: cc2f9c6b253b
Revises: 76f4d5475fb1
Create Date: 2020-06-21 08:38:31.933039

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "cc2f9c6b253b"
down_revision = "76f4d5475fb1"
branch_labels = None
depends_on = None


def upgrade():

    op.alter_column(
        "force_fields", column_name="inner_xml", new_column_name="inner_content",
    )


def downgrade():

    op.alter_column(
        "force_fields", column_name="inner_content", new_column_name="inner_xml",
    )
