"""add sendbird_channel_url to chat_sessions

Revision ID: add_sendbird_channel
Revises: chat_001
Create Date: 2025-12-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_sendbird_channel'
down_revision: Union[str, None] = 'chat_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sendbird_channel_url column to chat_sessions table
    op.add_column('chat_sessions', sa.Column('sendbird_channel_url', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove sendbird_channel_url column from chat_sessions table
    op.drop_column('chat_sessions', 'sendbird_channel_url')
