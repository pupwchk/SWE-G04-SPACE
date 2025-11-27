"""Add HRV, appliance, weather, and geofence models

Revision ID: 81c03ade5e0d
Revises: fatigue_001
Create Date: 2025-11-26 13:54:39.073599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '81c03ade5e0d'
down_revision: Union[str, None] = 'fatigue_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
