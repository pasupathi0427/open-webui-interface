"""CUSTOM: merge heads — custom chain (c3e9a1f7d2b5) + upstream v0.12.4 chain (0bd252b206fb)

Both branches start from b8f2c6d91a04. A merge revision (instead of re-parenting c3e9a1f7d2b5)
keeps databases that already applied the custom migrations correct: upgrading runs the upstream
v0.12.4 migrations they have not seen yet (c92da83b017f, 0bd252b206fb), then lands here.

Revision ID: e5b7d2c94f18
Revises: c3e9a1f7d2b5, 0bd252b206fb
Create Date: 2026-10-29 00:00:00.000000

"""

revision = 'e5b7d2c94f18'
down_revision = ('c3e9a1f7d2b5', '0bd252b206fb')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
