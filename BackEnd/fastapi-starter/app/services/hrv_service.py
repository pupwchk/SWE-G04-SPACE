"""
HRV (Heart Rate Variability) 서비스
애플워치에서 측정한 HRV 값을 동기화하고 피로도를 계산
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.hrv import HRVLog, FatigueHistory

logger = logging.getLogger(__name__)


class HRVService:
    """HRV 관리 및 피로도 계산 서비스"""

    @staticmethod
    def calculate_fatigue_from_hrv(hrv_value: float) -> int:
        """
        HRV 값으로부터 피로도 레벨 계산

        Args:
            hrv_value: HRV 값 (ms)

        Returns:
            피로도 레벨 (1: 좋음, 2: 보통, 3: 나쁨, 4: 매우 나쁨)
        """
        if hrv_value >= 34:
            return 1  # 좋음
        elif hrv_value >= 21:
            return 2  # 보통
        elif hrv_value >= 15:
            return 3  # 나쁨
        else:
            return 4  # 매우 나쁨

    @staticmethod
    def sync_hrv_from_healthkit(
        db: Session,
        user_id,  # str or UUID
        hrv_value: float,
        measured_at: datetime
    ) -> HRVLog:
        """
        HealthKit에서 받은 HRV 데이터를 동기화

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            hrv_value: HRV 값 (ms)
            measured_at: 측정 시각

        Returns:
            생성된 HRVLog
        """
        fatigue_level = HRVService.calculate_fatigue_from_hrv(hrv_value)

        hrv_log = HRVLog(
            user_id=user_id,
            hrv_value=hrv_value,
            fatigue_level=fatigue_level,
            measured_at=measured_at
        )

        db.add(hrv_log)
        db.commit()
        db.refresh(hrv_log)

        logger.info(f"✅ HRV synced: user={user_id}, hrv={hrv_value}ms, fatigue={fatigue_level}")

        return hrv_log

    @staticmethod
    def get_latest_fatigue_level(db: Session, user_id) -> Optional[int]:  # str or UUID
        """
        사용자의 최신 피로도 레벨 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID

        Returns:
            피로도 레벨 (1~4) 또는 None (데이터 없음)
        """
        latest_log = db.query(HRVLog)\
            .filter(HRVLog.user_id == user_id)\
            .order_by(desc(HRVLog.measured_at))\
            .first()

        if latest_log:
            return latest_log.fatigue_level

        logger.warning(f"⚠️ No HRV data found for user {user_id}")
        return None

    @staticmethod
    def get_latest_hrv_log(db: Session, user_id) -> Optional[HRVLog]:  # str or UUID
        """
        사용자의 최신 HRV 로그 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID

        Returns:
            HRVLog 또는 None
        """
        return db.query(HRVLog)\
            .filter(HRVLog.user_id == user_id)\
            .order_by(desc(HRVLog.measured_at))\
            .first()

    @staticmethod
    def get_hrv_history(
        db: Session,
        user_id,  # str or UUID
        days: int = 7
    ) -> list[HRVLog]:
        """
        사용자의 HRV 히스토리 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            days: 조회할 일수

        Returns:
            HRVLog 리스트
        """
        since = datetime.now() - timedelta(days=days)

        return db.query(HRVLog)\
            .filter(
                HRVLog.user_id == user_id,
                HRVLog.measured_at >= since
            )\
            .order_by(desc(HRVLog.measured_at))\
            .all()

    @staticmethod
    def calculate_average_fatigue(
        db: Session,
        user_id,  # str or UUID
        days: int = 7
    ) -> Optional[float]:
        """
        최근 N일간 평균 피로도 계산

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            days: 조회할 일수

        Returns:
            평균 피로도 (1.0 ~ 4.0) 또는 None
        """
        logs = HRVService.get_hrv_history(db, user_id, days)

        if not logs:
            return None

        avg = sum(log.fatigue_level for log in logs) / len(logs)
        return round(avg, 2)


# 싱글톤 인스턴스
hrv_service = HRVService()
