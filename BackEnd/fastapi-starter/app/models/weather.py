"""
날씨 캐시 모델
"""
import uuid
from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.config.db import Base


class WeatherCache(Base):
    """날씨 데이터 캐시"""
    __tablename__ = "weather_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 위치 키 (위도경도 해시)
    location_key = Column(String, nullable=False, unique=True, index=True, comment="위도경도 조합 (예: 37.5665_126.9780)")

    # 기상청 초단기실황 데이터
    temperature = Column(Float, nullable=True, comment="기온 (°C)")
    humidity = Column(Float, nullable=True, comment="습도 (%)")
    precipitation = Column(Float, nullable=True, comment="1시간 강수량 (mm)")
    wind_speed = Column(Float, nullable=True, comment="풍속 (m/s)")

    # 미세먼지 데이터
    pm10 = Column(Float, nullable=True, comment="미세먼지 PM10 (㎍/㎥)")
    pm2_5 = Column(Float, nullable=True, comment="초미세먼지 PM2.5 (㎍/㎥)")

    # 메타데이터
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="조회 시각")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="만료 시각 (보통 10분 후)")

    __table_args__ = (
        Index('idx_weather_location_fetched', 'location_key', 'fetched_at'),
    )
