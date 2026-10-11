"""CUSTOM: merge heads — usage tables (a7f3c2e1b9d4) + upstream v0.12.0 chain (b8f2c6d91a04)

Both branches start from d4c1a8e37b62. A merge revision (instead of re-parenting a7f3c2e1b9d4)
keeps databases that already applied the usage tables correct: upgrading runs the upstream
v0.12.0 migrations they have not seen yet, then lands here.

Revision ID: c3e9a1f7d2b5
Revises: a7f3c2e1b9d4, b8f2c6d91a04
Create Date: 2026-10-11 00:00:00.000000

"""

revision = 'c3e9a1f7d2b5'
down_revision = ('a7f3c2e1b9d4', 'b8f2c6d91a04')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
