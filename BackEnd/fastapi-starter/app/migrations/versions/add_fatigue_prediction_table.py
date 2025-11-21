"""add fatigue prediction table

Revision ID: fatigue_001
Revises: 63773ec0a32a
Create Date: 2025-11-14 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fatigue_001'
down_revision: Union[str, None] = '63773ec0a32a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create fatigue_predictions table
    op.create_table(
        'fatigue_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fatigue_level', sa.String(), nullable=False),
        sa.Column('fatigue_class', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('class_probabilities', postgresql.JSONB(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indices
    op.create_index(
        'ix_fatigue_predictions_user_id',
        'fatigue_predictions',
        ['user_id']
    )
    op.create_index(
        'ix_fatigue_predictions_timestamp',
        'fatigue_predictions',
        ['timestamp']
    )


def downgrade() -> None:
    # Drop indices
    op.drop_index('ix_fatigue_predictions_timestamp', 'fatigue_predictions')
    op.drop_index('ix_fatigue_predictions_user_id', 'fatigue_predictions')

    # Drop table
    op.drop_table('fatigue_predictions')
