"""
Geofence 서비스 - GPS 기반 위치 트리거 및 Approaching 감지
"""
import math
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.location import UserLocation, GeofenceTracking, GeofenceEvent
from app.config.sendbird import SendbirdConfig

logger = logging.getLogger(__name__)


class GeofenceService:
    """Geofence 관리 서비스 (DB 기반)"""

    def __init__(self):
        # 환경변수에서 기본 집 위치 로드
        self.default_home_lat = SendbirdConfig.HOME_LATITUDE
        self.default_home_lng = SendbirdConfig.HOME_LONGITUDE
        self.default_radius = SendbirdConfig.GEOFENCE_RADIUS_METERS

    @staticmethod
    def haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Haversine 공식으로 두 GPS 좌표 간 거리 계산

        Args:
            lat1, lon1: 첫 번째 좌표
            lat2, lon2: 두 번째 좌표

        Returns:
            거리 (미터)
        """
        # 지구 반지름 (미터)
        R = 6371000

        # 라디안 변환
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        # Haversine 공식
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(delta_lambda / 2) ** 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    def get_user_location_settings(self, db: Session, user_id: str) -> UserLocation:
        """
        사용자 위치 설정 조회 (없으면 생성)

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID

        Returns:
            UserLocation 객체
        """
        location = db.query(UserLocation)\
            .filter(UserLocation.user_id == user_id)\
            .first()

        if not location:
            # 기본값으로 생성
            location = UserLocation(
                user_id=user_id,
                home_latitude=self.default_home_lat,
                home_longitude=self.default_home_lng,
                geofence_radius_meters=self.default_radius
            )
            db.add(location)
            db.commit()
            db.refresh(location)
            logger.info(f"📍 Created default location settings for user {user_id}")

        return location

    def update_home_location(
        self,
        db: Session,
        user_id: str,
        latitude: float,
        longitude: float,
        radius_meters: Optional[float] = None
    ) -> UserLocation:
        """
        집 위치 업데이트

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            latitude: 집 위도
            longitude: 집 경도
            radius_meters: Geofence 반경 (미터)

        Returns:
            업데이트된 UserLocation
        """
        location = self.get_user_location_settings(db, user_id)

        location.home_latitude = latitude
        location.home_longitude = longitude

        if radius_meters is not None:
            location.geofence_radius_meters = radius_meters

        db.commit()
        db.refresh(location)

        logger.info(f"🏠 Updated home location for {user_id}: ({latitude}, {longitude}), radius={location.geofence_radius_meters}m")

        return location

    def calculate_distance_to_home(
        self,
        db: Session,
        user_id: str,
        user_lat: float,
        user_lng: float
    ) -> float:
        """
        사용자 위치에서 집까지 거리 계산

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            user_lat: 사용자 위도
            user_lng: 사용자 경도

        Returns:
            거리 (미터)
        """
        location = self.get_user_location_settings(db, user_id)

        if not location.home_latitude or not location.home_longitude:
            logger.warning(f"⚠️ User {user_id} has no home location set")
            return float('inf')

        return self.haversine_distance(
            user_lat, user_lng,
            location.home_latitude, location.home_longitude
        )

    def is_inside_geofence(
        self,
        db: Session,
        user_id: str,
        distance: float
    ) -> bool:
        """
        Geofence 내부에 있는지 확인

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            distance: 집까지 거리

        Returns:
            True if inside geofence
        """
        location = self.get_user_location_settings(db, user_id)
        return distance <= location.geofence_radius_meters

    def detect_approaching(
        self,
        db: Session,
        user_id: str,
        current_distance: float,
        lookback_minutes: int = 30
    ) -> bool:
        """
        집에 접근 중인지 감지 (지속적으로 가까워지는지 확인)

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            current_distance: 현재 집까지 거리
            lookback_minutes: 과거 몇 분을 확인할지 (기본 30분)

        Returns:
            True if approaching (지속적으로 가까워지는 중)
        """
        # 최근 기록 조회
        since = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)

        recent_tracks = db.query(GeofenceTracking)\
            .filter(
                GeofenceTracking.user_id == user_id,
                GeofenceTracking.tracked_at >= since
            )\
            .order_by(desc(GeofenceTracking.tracked_at))\
            .limit(3)\
            .all()

        if len(recent_tracks) < 2:
            # 데이터 부족
            return False

        # 최근 3개 기록이 모두 가까워지는 추세인지 확인
        # (현재 거리가 이전 기록들보다 짧아지고 있는지)
        is_approaching = True

        for track in recent_tracks:
            if current_distance >= track.distance_from_home:
                # 이전보다 멀어졌거나 같음
                is_approaching = False
                break

        if is_approaching:
            logger.info(f"🏃 User {user_id} is approaching home (distance: {current_distance:.1f}m)")

        return is_approaching

    def track_location(
        self,
        db: Session,
        user_id: str,
        latitude: float,
        longitude: float,
        accuracy: Optional[float] = None
    ) -> GeofenceTracking:
        """
        위치 추적 기록 저장 (10분 간격)

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            latitude: 위도
            longitude: 경도
            accuracy: GPS 정확도 (미터)

        Returns:
            GeofenceTracking 객체
        """
        # 거리 계산
        distance = self.calculate_distance_to_home(db, user_id, latitude, longitude)

        # 접근 중인지 감지
        approaching = self.detect_approaching(db, user_id, distance)

        # 이전 거리 조회
        last_track = db.query(GeofenceTracking)\
            .filter(GeofenceTracking.user_id == user_id)\
            .order_by(desc(GeofenceTracking.tracked_at))\
            .first()

        previous_distance = last_track.distance_from_home if last_track else None

        # 추적 기록 저장
        tracking = GeofenceTracking(
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            distance_from_home=distance,
            approaching=approaching,
            previous_distance=previous_distance
        )

        db.add(tracking)
        db.commit()
        db.refresh(tracking)

        logger.info(f"📍 Tracked: user={user_id}, distance={distance:.1f}m, approaching={approaching}")

        return tracking

    def check_geofence_trigger(
        self,
        db: Session,
        user_id: str,
        latitude: float,
        longitude: float,
        accuracy: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Geofence 트리거 확인 및 이벤트 기록

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            latitude: 위도
            longitude: 경도
            accuracy: GPS 정확도 (미터)

        Returns:
            {
                "triggered": bool,
                "event": "ENTER" | "EXIT" | "APPROACHING_DETECTED" | None,
                "distance": float,
                "inside_geofence": bool,
                "approaching": bool
            }
        """
        # 위치 추적 기록
        tracking = self.track_location(db, user_id, latitude, longitude, accuracy)

        distance = tracking.distance_from_home
        inside = self.is_inside_geofence(db, user_id, distance)
        approaching = tracking.approaching

        # 이전 상태 조회 (마지막 이벤트 기준)
        last_event = db.query(GeofenceEvent)\
            .filter(GeofenceEvent.user_id == user_id)\
            .order_by(desc(GeofenceEvent.created_at))\
            .first()

        # 최근 ENTER 이벤트가 있는지 확인 (중복 방지)
        recent_enter = None
        if last_event:
            time_since_last = datetime.now(timezone.utc) - last_event.created_at
            if last_event.event_type == "ENTER" and time_since_last < timedelta(minutes=30):
                recent_enter = last_event

        # 상태 변화 감지
        triggered = False
        event_type = None

        # APPROACHING_DETECTED 이벤트 (집에 접근 중)
        if approaching and not inside:
            # 최근 30분 내에 APPROACHING_DETECTED 이벤트가 없으면 트리거
            recent_approaching = db.query(GeofenceEvent)\
                .filter(
                    GeofenceEvent.user_id == user_id,
                    GeofenceEvent.event_type == "APPROACHING_DETECTED",
                    GeofenceEvent.created_at >= datetime.now(timezone.utc) - timedelta(minutes=30)
                )\
                .first()

            if not recent_approaching:
                triggered = True
                event_type = "APPROACHING_DETECTED"
                logger.info(f"🏃 User {user_id} approaching home (distance: {distance:.1f}m)")

        # ENTER 이벤트 (Geofence 진입)
        elif inside and not recent_enter:
            triggered = True
            event_type = "ENTER"
            logger.info(f"🏠 User {user_id} entered geofence (distance: {distance:.1f}m)")

        # EXIT 이벤트 (Geofence 이탈)
        elif not inside and last_event and last_event.event_type == "ENTER":
            time_since_enter = datetime.now(timezone.utc) - last_event.created_at
            # 진입 후 최소 10분 후에만 EXIT 기록 (짧은 출입 무시)
            if time_since_enter >= timedelta(minutes=10):
                triggered = True
                event_type = "EXIT"
                logger.info(f"🚶 User {user_id} exited geofence (distance: {distance:.1f}m)")

        # 이벤트 기록
        if triggered and event_type:
            event = GeofenceEvent(
                user_id=user_id,
                event_type=event_type,
                distance_from_home=distance,
                triggered_scenario1=False  # 시나리오 1 트리거는 별도 처리
            )
            db.add(event)
            db.commit()
            db.refresh(event)

        return {
            "triggered": triggered,
            "event": event_type,
            "distance": distance,
            "inside_geofence": inside,
            "approaching": approaching,
            "accuracy": accuracy
        }

    def get_recent_events(
        self,
        db: Session,
        user_id: str,
        hours: int = 24
    ) -> list[GeofenceEvent]:
        """
        최근 Geofence 이벤트 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            hours: 조회할 시간 범위 (기본 24시간)

        Returns:
            GeofenceEvent 리스트
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        return db.query(GeofenceEvent)\
            .filter(
                GeofenceEvent.user_id == user_id,
                GeofenceEvent.created_at >= since
            )\
            .order_by(desc(GeofenceEvent.created_at))\
            .all()


# 싱글톤 인스턴스
geofence_service = GeofenceService()
