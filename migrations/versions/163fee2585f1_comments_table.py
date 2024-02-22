"""comments table

Revision ID: 163fee2585f1
Revises: 59cb9a4cdabe
Create Date: 2024-02-18 14:51:58.045020

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "163fee2585f1"
down_revision = "59cb9a4cdabe"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("post_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["posts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("comments")
    # ### end Alembic commands ###
