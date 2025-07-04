"""Add label_options to Recipe

Revision ID: 5a26590d5487
Revises: a54739f9f32d
Create Date: 2025-06-20 21:05:33.721880

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a26590d5487'
down_revision = 'a54739f9f32d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('label_options', sa.JSON(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.drop_column('label_options')

    # ### end Alembic commands ###
