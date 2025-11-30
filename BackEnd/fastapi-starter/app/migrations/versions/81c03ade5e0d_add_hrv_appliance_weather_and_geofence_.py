"""Add HRV, appliance, weather, and geofence models

Revision ID: 81c03ade5e0d
Revises: fatigue_001
Create Date: 2025-11-26 13:54:39.073599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '81c03ade5e0d'
down_revision: Union[str, None] = 'fatigue_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create appliances table
    op.create_table('appliances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('place_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('appliance_code', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('vendor', sa.String(), nullable=True),
        sa.Column('model_name', sa.String(), nullable=True),
        sa.Column('external_device_id', sa.String(), nullable=True),
        sa.Column('connection_type', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['place_id'], ['places.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_appliances_user_id_appliance_code', 'appliances', ['user_id', 'appliance_code'], unique=False)
    op.create_index('ix_appliances_user_id_place_id', 'appliances', ['user_id', 'place_id'], unique=False)

    # Create air_conditioner_configs table
    op.create_table('air_conditioner_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appliance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('power_state', sa.String(), nullable=False),
        sa.Column('mode', sa.String(), nullable=True),
        sa.Column('target_temp_c', sa.Float(), nullable=True),
        sa.Column('fan_speed', sa.String(), nullable=True),
        sa.Column('swing_mode', sa.String(), nullable=True),
        sa.Column('target_humidity_pct', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['appliance_id'], ['appliances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appliance_id', name='uq_air_conditioner_configs_appliance_id')
    )

    # Create tv_configs table
    op.create_table('tv_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appliance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('power_state', sa.String(), nullable=False),
        sa.Column('volume', sa.Integer(), nullable=True),
        sa.Column('channel', sa.Integer(), nullable=True),
        sa.Column('input_source', sa.String(), nullable=True),
        sa.Column('brightness', sa.Integer(), nullable=True),
        sa.Column('contrast', sa.Integer(), nullable=True),
        sa.Column('color', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['appliance_id'], ['appliances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appliance_id', name='uq_tv_configs_appliance_id')
    )

    # Create air_purifier_configs table
    op.create_table('air_purifier_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appliance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('power_state', sa.String(), nullable=False),
        sa.Column('mode', sa.String(), nullable=True),
        sa.Column('fan_speed', sa.String(), nullable=True),
        sa.Column('ionizer_on', sa.Boolean(), nullable=True),
        sa.Column('target_pm10', sa.Integer(), nullable=True),
        sa.Column('target_pm2_5', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['appliance_id'], ['appliances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appliance_id', name='uq_air_purifier_configs_appliance_id')
    )

    # Create light_configs table
    op.create_table('light_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appliance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('power_state', sa.String(), nullable=False),
        sa.Column('brightness_pct', sa.Integer(), nullable=True),
        sa.Column('color_temperature_k', sa.Integer(), nullable=True),
        sa.Column('color_hex', sa.String(), nullable=True),
        sa.Column('scene', sa.String(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['appliance_id'], ['appliances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appliance_id', name='uq_light_configs_appliance_id')
    )

    # Create humidifier_configs table
    op.create_table('humidifier_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appliance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('power_state', sa.String(), nullable=False),
        sa.Column('mode', sa.String(), nullable=True),
        sa.Column('mist_level', sa.Integer(), nullable=True),
        sa.Column('target_humidity_pct', sa.Integer(), nullable=True),
        sa.Column('warm_mist', sa.Boolean(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['appliance_id'], ['appliances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appliance_id', name='uq_humidifier_configs_appliance_id')
    )

    # Create characters table
    op.create_table('characters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nickname', sa.String(), nullable=False),
        sa.Column('persona', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('characters')
    op.drop_table('humidifier_configs')
    op.drop_table('light_configs')
    op.drop_table('air_purifier_configs')
    op.drop_table('tv_configs')
    op.drop_table('air_conditioner_configs')
    op.drop_index('ix_appliances_user_id_place_id', table_name='appliances')
    op.drop_index('ix_appliances_user_id_appliance_code', table_name='appliances')
    op.drop_table('appliances')
