"""
HRV (Heart Rate Variability) 및 피로도 관련 모델
"""
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.db import Base


class HRVLog(Base):
    """HRV 측정 로그"""
    __tablename__ = "hrv_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # HRV 데이터
    hrv_value = Column(Float, nullable=False, comment="HRV 값 (ms)")
    fatigue_level = Column(Integer, nullable=False, comment="피로도 레벨 (1: 좋음, 2: 보통, 3: 나쁨, 4: 매우 나쁨)")

    # 타임스탬프
    measured_at = Column(DateTime(timezone=True), nullable=False, comment="애플워치에서 측정한 시각")
    synced_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="백엔드에 동기화된 시각")

    # 인덱스: 사용자별 최신 데이터 조회용
    __table_args__ = (
        Index('idx_hrv_user_measured', 'user_id', 'measured_at'),
    )


class FatigueHistory(Base):
    """피로도 변화 히스토리 (집계용)"""
    __tablename__ = "fatigue_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    date = Column(DateTime(timezone=True), nullable=False, comment="날짜")
    avg_hrv = Column(Float, nullable=True, comment="평균 HRV")
    avg_fatigue_level = Column(Float, nullable=True, comment="평균 피로도")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_fatigue_history_user_date', 'user_id', 'date'),
    )
