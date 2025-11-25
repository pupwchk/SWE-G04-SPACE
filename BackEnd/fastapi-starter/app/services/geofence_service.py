"""
Geofence 서비스 - GPS 기반 위치 트리거
"""
import math
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.config.sendbird import SendbirdConfig

logger = logging.getLogger(__name__)


class GeofenceService:
    """Geofence 관리 서비스"""
    
    def __init__(self):
        self.home_lat = SendbirdConfig.HOME_LATITUDE
        self.home_lng = SendbirdConfig.HOME_LONGITUDE
        self.radius = SendbirdConfig.GEOFENCE_RADIUS_METERS
        
        # 사용자별 마지막 상태 추적 (DB에 저장해야 함)
        self.user_states: Dict[str, Dict] = {}
    
    def haversine_distance(
        self,
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
    
    def calculate_distance_to_home(
        self,
        user_lat: float,
        user_lng: float
    ) -> float:
        """
        사용자 위치에서 집까지 거리 계산
        
        Args:
            user_lat: 사용자 위도
            user_lng: 사용자 경도
        
        Returns:
            거리 (미터)
        """
        return self.haversine_distance(
            user_lat, user_lng,
            self.home_lat, self.home_lng
        )
    
    def is_inside_geofence(
        self,
        user_lat: float,
        user_lng: float
    ) -> bool:
        """
        Geofence 내부에 있는지 확인
        
        Args:
            user_lat: 사용자 위도
            user_lng: 사용자 경도
        
        Returns:
            True if inside geofence
        """
        distance = self.calculate_distance_to_home(user_lat, user_lng)
        return distance <= self.radius
    
    def check_geofence_trigger(
        self,
        user_id: str,
        latitude: float,
        longitude: float,
        accuracy: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Geofence 트리거 확인
        
        Args:
            user_id: 사용자 ID
            latitude: 위도
            longitude: 경도
            accuracy: GPS 정확도 (미터)
        
        Returns:
            {
                "triggered": bool,
                "event": "ENTER" | "EXIT" | None,
                "distance": float,
                "inside_geofence": bool
            }
        """
        # 거리 계산
        distance = self.calculate_distance_to_home(latitude, longitude)
        inside = self.is_inside_geofence(latitude, longitude)
        
        # 이전 상태 조회
        previous_state = self.user_states.get(user_id, {})
        was_inside = previous_state.get("inside_geofence", False)
        
        # 상태 변화 감지
        triggered = False
        event = None
        
        if inside and not was_inside:
            # Geofence 진입
            triggered = True
            event = "ENTER"
            logger.info(f"🏠 User {user_id} entered geofence (distance: {distance:.1f}m)")
        
        elif not inside and was_inside:
            # Geofence 이탈
            triggered = True
            event = "EXIT"
            logger.info(f"🚶 User {user_id} exited geofence (distance: {distance:.1f}m)")
        
        # 상태 업데이트
        self.user_states[user_id] = {
            "inside_geofence": inside,
            "distance": distance,
            "last_update": datetime.now().isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": accuracy
        }
        
        return {
            "triggered": triggered,
            "event": event,
            "distance": distance,
            "inside_geofence": inside,
            "accuracy": accuracy
        }
    
    def get_user_state(self, user_id: str) -> Optional[Dict]:
        """사용자 현재 상태 조회"""
        return self.user_states.get(user_id)
    
    def set_home_location(self, latitude: float, longitude: float):
        """집 위치 설정"""
        self.home_lat = latitude
        self.home_lng = longitude
        logger.info(f"🏠 Home location updated: ({latitude}, {longitude})")
    
    def set_geofence_radius(self, radius_meters: float):
        """Geofence 반경 설정"""
        self.radius = radius_meters
        logger.info(f"📍 Geofence radius updated: {radius_meters}m")


# 싱글톤 인스턴스
geofence_service = GeofenceService()
