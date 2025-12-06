"""add_is_learned_to_user_appliance_preference

Revision ID: aea74eef514b
Revises: add_sendbird_channel
Create Date: 2025-12-06 13:57:30.364477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aea74eef514b'
down_revision: Union[str, None] = 'add_sendbird_channel'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user_appliance_preferences 테이블에 is_learned 컬럼 추가
    op.add_column('user_appliance_preferences',
                  sa.Column('is_learned', sa.Boolean(), nullable=False, server_default='false'))

    # 기존 데이터는 모두 is_learned = false (기본값)로 설정됨
    # 사용자가 실제로 승인/수정한 데이터만 is_learned = true로 변경됨


def downgrade() -> None:
    # is_learned 컬럼 제거
    op.drop_column('user_appliance_preferences', 'is_learned')
