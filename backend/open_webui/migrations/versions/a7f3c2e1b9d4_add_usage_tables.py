"""CUSTOM: add usage_config, usage_ledger, usage_request tables (token governance)

Revision ID: a7f3c2e1b9d4
Revises: d4c1a8e37b62
Create Date: 2026-10-06 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = 'a7f3c2e1b9d4'
down_revision = 'd4c1a8e37b62'
branch_labels = None
depends_on = None


def upgrade():
    tables = sa.inspect(op.get_bind()).get_table_names()

    if 'usage_config' not in tables:
        op.create_table(
            'usage_config',
            sa.Column('group_id', sa.Text(), primary_key=True),
            sa.Column('token_limit', sa.BigInteger(), nullable=False),
            sa.Column('resets_per_period', sa.Integer(), nullable=False),
            sa.Column('period_start', sa.BigInteger(), nullable=False),
            sa.Column('overrides', sa.JSON(), nullable=True),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
        )

    if 'usage_ledger' not in tables:
        op.create_table(
            'usage_ledger',
            sa.Column('id', sa.Text(), primary_key=True),
            sa.Column('user_id', sa.Text(), nullable=False),
            sa.Column('tokens', sa.BigInteger(), nullable=False),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
        )
        op.create_index('usage_ledger_user_created_idx', 'usage_ledger', ['user_id', 'created_at'])

    if 'usage_request' not in tables:
        op.create_table(
            'usage_request',
            sa.Column('id', sa.Text(), primary_key=True),
            sa.Column('user_id', sa.Text(), nullable=False),
            sa.Column('group_id', sa.Text(), nullable=True),
            sa.Column('period_start', sa.BigInteger(), nullable=False),
            sa.Column('status', sa.Text(), nullable=False),
            sa.Column('action', sa.Text(), nullable=True),
            sa.Column('tokens', sa.BigInteger(), nullable=True),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.Column('decided_at', sa.BigInteger(), nullable=True),
            sa.Column('decided_by', sa.Text(), nullable=True),
        )
        op.create_index('ix_usage_request_user_id', 'usage_request', ['user_id'])


def downgrade():
    op.drop_index('ix_usage_request_user_id', table_name='usage_request')
    op.drop_table('usage_request')
    op.drop_index('usage_ledger_user_created_idx', table_name='usage_ledger')
    op.drop_table('usage_ledger')
    op.drop_table('usage_config')
