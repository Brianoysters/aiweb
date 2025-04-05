"""merge heads and add course model

Revision ID: 5f2a09fdce99
Revises: 76a3d59c1e95, add_admin_and_payment, add_admin_payment_fields, add_payment_status
Create Date: 2025-04-05 22:19:41.148175

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f2a09fdce99'
down_revision = ('76a3d59c1e95', 'add_admin_and_payment', 'add_admin_payment_fields', 'add_payment_status')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
