"""add tracking and info models

Revision ID: 4b8c9d0e2f5a
Revises: 3ab07a8e1cd4
Create Date: 2025-11-28 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4b8c9d0e2f5a'
down_revision: Union[str, None] = '3ab07a8e1cd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create places table
    op.create_table('places',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('center_lat', sa.Float(), nullable=False),
        sa.Column('center_lon', sa.Float(), nullable=False),
        sa.Column('radius_m', sa.Float(), nullable=False),
        sa.Column('visits_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_places_user_id'), 'places', ['user_id'], unique=False)

    # Create time_slots table
    op.create_table('time_slots',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('ts_hour', sa.DateTime(timezone=True), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('altitude', sa.Float(), nullable=True),
        sa.Column('horizontal_accuracy', sa.Float(), nullable=True),
        sa.Column('vertical_accuracy', sa.Float(), nullable=True),
        sa.Column('place_id', sa.UUID(), nullable=True),
        sa.Column('grid_nx', sa.Integer(), nullable=True),
        sa.Column('grid_ny', sa.Integer(), nullable=True),
        sa.Column('weather_provider', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['place_id'], ['places.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'ts_hour', name='uq_time_slots_user_hour')
    )
    op.create_index(op.f('ix_time_slots_user_id'), 'time_slots', ['user_id'], unique=False)
    op.create_index(op.f('ix_time_slots_ts_hour'), 'time_slots', ['ts_hour'], unique=False)
    op.create_index(op.f('ix_time_slots_place_id'), 'time_slots', ['place_id'], unique=False)

    # Create weather_observations table
    op.create_table('weather_observations',
        sa.Column('nx', sa.Integer(), nullable=False),
        sa.Column('ny', sa.Integer(), nullable=False),
        sa.Column('as_of', sa.DateTime(timezone=True), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('condition_code', sa.String(), nullable=True),
        sa.Column('precip_type', sa.String(), nullable=True),
        sa.Column('temp_c', sa.Float(), nullable=True),
        sa.Column('humidity_pct', sa.Float(), nullable=True),
        sa.Column('wind_speed_mps', sa.Float(), nullable=True),
        sa.Column('pm10', sa.Float(), nullable=True),
        sa.Column('pm2_5', sa.Float(), nullable=True),
        sa.Column('raw_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('nx', 'ny', 'as_of', 'provider')
    )

    # Create sleep_sessions table
    op.create_table('sleep_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('in_bed_hr', sa.Float(), nullable=True),
        sa.Column('asleep_hr', sa.Float(), nullable=True),
        sa.Column('awake_hr', sa.Float(), nullable=True),
        sa.Column('core_hr', sa.Float(), nullable=True),
        sa.Column('deep_hr', sa.Float(), nullable=True),
        sa.Column('rem_hr', sa.Float(), nullable=True),
        sa.Column('respiratory_rate', sa.Float(), nullable=True),
        sa.Column('heart_rate_avg', sa.Float(), nullable=True),
        sa.Column('efficiency', sa.Float(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('device_model', sa.String(), nullable=True),
        sa.Column('os_version', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'start_at', 'end_at', name='uq_sleep_user_period')
    )
    op.create_index(op.f('ix_sleep_sessions_user_id'), 'sleep_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_sleep_sessions_start_at'), 'sleep_sessions', ['start_at'], unique=False)
    op.create_index(op.f('ix_sleep_sessions_end_at'), 'sleep_sessions', ['end_at'], unique=False)

    # Create workout_sessions table
    op.create_table('workout_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('workout_type', sa.String(), nullable=False),
        sa.Column('step_count', sa.Integer(), nullable=True),
        sa.Column('distance_km', sa.Float(), nullable=True),
        sa.Column('flights_climbed', sa.Integer(), nullable=True),
        sa.Column('active_energy_kcal', sa.Float(), nullable=True),
        sa.Column('basal_energy_kcal', sa.Float(), nullable=True),
        sa.Column('exercise_min', sa.Float(), nullable=True),
        sa.Column('stand_hr', sa.Float(), nullable=True),
        sa.Column('stand_hours', sa.Integer(), nullable=True),
        sa.Column('walking_speed_kmh', sa.Float(), nullable=True),
        sa.Column('step_length_cm', sa.Float(), nullable=True),
        sa.Column('walking_asymmetry_pct', sa.Float(), nullable=True),
        sa.Column('double_support_pct', sa.Float(), nullable=True),
        sa.Column('stair_speed_up_dps', sa.Float(), nullable=True),
        sa.Column('stair_speed_down_dps', sa.Float(), nullable=True),
        sa.Column('avg_hr', sa.Float(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('device_model', sa.String(), nullable=True),
        sa.Column('os_version', sa.String(), nullable=True),
        sa.Column('meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workout_sessions_user_id'), 'workout_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_workout_sessions_start_at'), 'workout_sessions', ['start_at'], unique=False)
    op.create_index(op.f('ix_workout_sessions_end_at'), 'workout_sessions', ['end_at'], unique=False)

    # Create health_hourly table
    op.create_table('health_hourly',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('ts_hour', sa.DateTime(timezone=True), nullable=False),
        sa.Column('heart_rate_bpm', sa.Float(), nullable=True),
        sa.Column('resting_hr_bpm', sa.Float(), nullable=True),
        sa.Column('walking_hr_avg_bpm', sa.Float(), nullable=True),
        sa.Column('hrv_sdnn_ms', sa.Float(), nullable=True),
        sa.Column('vo2_max', sa.Float(), nullable=True),
        sa.Column('spo2_pct', sa.Float(), nullable=True),
        sa.Column('ecg_index', sa.Float(), nullable=True),
        sa.Column('irregular_rhythm', sa.Boolean(), nullable=True),
        sa.Column('respiratory_rate_cpm', sa.Float(), nullable=True),
        sa.Column('oxygen_saturation_pct', sa.Float(), nullable=True),
        sa.Column('env_audio_db', sa.Float(), nullable=True),
        sa.Column('headphone_audio_db', sa.Float(), nullable=True),
        sa.Column('env_sound_level_db', sa.Float(), nullable=True),
        sa.Column('wrist_temp_c', sa.Float(), nullable=True),
        sa.Column('mindful_min', sa.Float(), nullable=True),
        sa.Column('daylight_min', sa.Float(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('device_model', sa.String(), nullable=True),
        sa.Column('os_version', sa.String(), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'ts_hour', name='uq_health_user_hour')
    )
    op.create_index(op.f('ix_health_hourly_user_id'), 'health_hourly', ['user_id'], unique=False)
    op.create_index(op.f('ix_health_hourly_ts_hour'), 'health_hourly', ['ts_hour'], unique=False)

    # Create appliances table (from info.py)
    op.create_table('appliances',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('place_id', sa.UUID(), nullable=True),
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
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('appliance_id', sa.UUID(), nullable=False),
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
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('appliance_id', sa.UUID(), nullable=False),
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
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('appliance_id', sa.UUID(), nullable=False),
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
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('appliance_id', sa.UUID(), nullable=False),
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
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('appliance_id', sa.UUID(), nullable=False),
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
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('nickname', sa.String(), nullable=False),
        sa.Column('persona', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('characters')
    op.drop_table('humidifier_configs')
    op.drop_table('light_configs')
    op.drop_table('air_purifier_configs')
    op.drop_table('tv_configs')
    op.drop_table('air_conditioner_configs')

    op.drop_index('ix_appliances_user_id_place_id', table_name='appliances')
    op.drop_index('ix_appliances_user_id_appliance_code', table_name='appliances')
    op.drop_table('appliances')

    op.drop_index(op.f('ix_health_hourly_ts_hour'), table_name='health_hourly')
    op.drop_index(op.f('ix_health_hourly_user_id'), table_name='health_hourly')
    op.drop_table('health_hourly')

    op.drop_index(op.f('ix_workout_sessions_end_at'), table_name='workout_sessions')
    op.drop_index(op.f('ix_workout_sessions_start_at'), table_name='workout_sessions')
    op.drop_index(op.f('ix_workout_sessions_user_id'), table_name='workout_sessions')
    op.drop_table('workout_sessions')

    op.drop_index(op.f('ix_sleep_sessions_end_at'), table_name='sleep_sessions')
    op.drop_index(op.f('ix_sleep_sessions_start_at'), table_name='sleep_sessions')
    op.drop_index(op.f('ix_sleep_sessions_user_id'), table_name='sleep_sessions')
    op.drop_table('sleep_sessions')

    op.drop_table('weather_observations')

    op.drop_index(op.f('ix_time_slots_place_id'), table_name='time_slots')
    op.drop_index(op.f('ix_time_slots_ts_hour'), table_name='time_slots')
    op.drop_index(op.f('ix_time_slots_user_id'), table_name='time_slots')
    op.drop_table('time_slots')

    op.drop_index(op.f('ix_places_user_id'), table_name='places')
    op.drop_table('places')
