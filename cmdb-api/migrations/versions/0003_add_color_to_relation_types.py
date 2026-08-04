# -*- coding:utf-8 -*-


"""add color to c_relation_types

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa


revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('c_relation_types', sa.Column('color', sa.String(7), nullable=False, server_default='#1890ff'))


def downgrade():
    op.drop_column('c_relation_types', 'color')
