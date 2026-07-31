# -*- coding:utf-8 -*-


"""add is_file to c_attributes

Revision ID: 0002
Revises: 6a4df2623057
Create Date: 2026-07-31
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '6a4df2623057'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('c_attributes', sa.Column('is_file', sa.Boolean(), server_default=sa.text('0'), nullable=True))


def downgrade():
    op.drop_column('c_attributes', 'is_file')
