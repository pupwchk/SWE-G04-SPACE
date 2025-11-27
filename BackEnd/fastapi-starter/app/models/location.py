"""
위치 추적 및 Geofence 모델
"""
import uuid
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.config.db import Base


class UserLocation(Base):
    """사용자 위치 정보"""
    __tablename__ = "user_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 집 위치
    home_latitude = Column(Float, nullable=True, comment="집 위도")
    home_longitude = Column(Float, nullable=True, comment="집 경도")

    # Geofence 설정
    geofence_radius_meters = Column(Float, nullable=False, server_default="100.0", comment="Geofence 반경 (미터)")

    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)


class GeofenceTracking(Base):
    """Geofence 추적 로그 (10분 단위)"""
    __tablename__ = "geofence_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 현재 위치
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # 집까지 거리
    distance_from_home = Column(Float, nullable=False, comment="집까지 거리 (미터)")

    # 접근 중 여부
    approaching = Column(Boolean, nullable=False, server_default="false", comment="지속적으로 가까워지는 중")

    # 이전 거리 (비교용)
    previous_distance = Column(Float, nullable=True, comment="10분 전 거리")

    tracked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_geofence_user_tracked', 'user_id', 'tracked_at'),
    )


class GeofenceEvent(Base):
    """Geofence 이벤트 (ENTER/EXIT)"""
    __tablename__ = "geofence_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String, nullable=False, comment="ENTER/EXIT/APPROACHING_DETECTED")
    distance_from_home = Column(Float, nullable=False)

    # 시나리오 1 트리거 여부
    triggered_scenario1 = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_geofence_event_user', 'user_id', 'event_type', 'created_at'),
    )
