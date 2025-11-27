"""
가전 제어 관련 모델
"""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.config.db import Base


class ApplianceConditionRule(Base):
    """가전 작동 조건 테이블 (사용자별 x 피로도별)"""
    __tablename__ = "appliance_condition_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 피로도 레벨 (1~4)
    fatigue_level = Column(Integer, nullable=False, comment="피로도 레벨 (1: 좋음, 2: 보통, 3: 나쁨, 4: 매우 나쁨)")

    # 가전 종류
    appliance_type = Column(String, nullable=False, comment="가전 종류 (에어컨/가습기/제습기/공기청정기/조명/TV)")

    # 작동 조건 (JSON)
    # 예: {"temp_threshold": 28, "operator": ">="}
    # 예: {"humidity_threshold": 30, "operator": "<=", "mode": "humidify"}
    condition_json = Column(JSON, nullable=False, comment="작동 조건")

    # 제어 액션 및 설정
    action = Column(String, nullable=False, server_default="on", comment="제어 액션 (on/off/auto)")
    settings_json = Column(JSON, nullable=True, comment="제어 설정값 (온도, 풍속 등)")
    priority = Column(Integer, nullable=False, server_default="1", comment="우선순위 (1이 가장 높음)")

    # 활성화 여부
    is_enabled = Column(Boolean, nullable=False, server_default="true", comment="이 규칙 활성화 여부")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    __table_args__ = (
        Index('idx_condition_user_fatigue', 'user_id', 'fatigue_level', 'appliance_type'),
    )


class UserAppliancePreference(Base):
    """사용자 선호 가전 세팅 (사용자별 x 피로도별)"""
    __tablename__ = "user_appliance_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 피로도 레벨 (1~4)
    fatigue_level = Column(Integer, nullable=False, comment="피로도 레벨")

    # 가전 종류
    appliance_type = Column(String, nullable=False, comment="가전 종류")

    # 선호 세팅 (JSON)
    # 에어컨: {"target_temp_c": 25, "fan_speed": "mid", "swing_mode": "both"}
    # 가습기: {"mode": "auto", "target_humidity_pct": 50}
    settings_json = Column(JSON, nullable=False, comment="선호 세팅")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    __table_args__ = (
        Index('idx_preference_user_fatigue', 'user_id', 'fatigue_level', 'appliance_type'),
    )


class ApplianceStatus(Base):
    """가상 가전 상태 (모니터링용)"""
    __tablename__ = "appliance_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    appliance_type = Column(String, nullable=False, comment="가전 종류")

    # 현재 상태
    is_on = Column(Boolean, nullable=False, server_default="false", comment="전원 상태")
    current_settings = Column(JSON, nullable=True, comment="현재 설정값")

    last_command = Column(JSON, nullable=True, comment="마지막 명령")
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_appliance_status_user', 'user_id', 'appliance_type'),
    )


class ApplianceCommandLog(Base):
    """가전 제어 명령 로그"""
    __tablename__ = "appliance_command_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    appliance_type = Column(String, nullable=False)
    action = Column(String, nullable=False, comment="on/off/set")
    settings = Column(JSON, nullable=True)

    # 실행 결과
    success = Column(Boolean, nullable=False)
    error_message = Column(String, nullable=True)

    # 컨텍스트
    triggered_by = Column(String, nullable=True, comment="scenario1/scenario2/manual")
    fatigue_level_used = Column(Integer, nullable=True)

    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_command_log_user_executed', 'user_id', 'executed_at'),
    )
