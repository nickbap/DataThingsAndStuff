"""rename user to users

Revision ID: ea71761413ea
Revises: 438b35e75b44
Create Date: 2021-10-11 13:58:51.710381

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ea71761413ea"
down_revision = "438b35e75b44"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("user", "users")


def downgrade():
    op.rename_table("users", "user")
