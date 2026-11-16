"""CUSTOM: merge heads — custom chain (e5b7d2c94f18) + upstream v0.13.3 chain (9f6c2a8d1b43)

Both branches start from the v0.12.4 head. A merge revision (instead of re-parenting) keeps
databases that already applied the custom migrations correct: upgrading runs the upstream
v0.13.3 migrations they have not seen yet, then lands here.

Revision ID: a7d4e2c19b60
Revises: e5b7d2c94f18, 9f6c2a8d1b43
Create Date: 2026-11-16 00:00:00.000000

"""

revision = 'a7d4e2c19b60'
down_revision = ('e5b7d2c94f18', '9f6c2a8d1b43')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
