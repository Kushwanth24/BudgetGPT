"""add category_id to expenses

Revision ID: 7bcaadebdded
Revises: c207d5e3f987
Create Date: 2026-02-01 22:32:45.597623

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7bcaadebdded'
down_revision = 'c207d5e3f987'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('expenses') as batch_op:
        batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_expenses_category_id'), ['category_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_expenses_category_id',
            'categories',
            ['category_id'],
            ['id']
        )

def downgrade():
    with op.batch_alter_table('expenses') as batch_op:
        batch_op.drop_constraint('fk_expenses_category_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_expenses_category_id'))
        batch_op.drop_column('category_id')


    # ### end Alembic commands ###
