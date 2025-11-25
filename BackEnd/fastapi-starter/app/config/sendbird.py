"""
Sendbird 설정 및 상수
"""

import os
from typing import Optional


class SendbirdConfig:
    """Sendbird 설정"""

    # Sendbird Application ID
    APP_ID: str = os.getenv("SENDBIRD_APP_ID", "YOUR_SENDBIRD_APP_ID")

    # Sendbird API Token
    API_TOKEN: str = os.getenv("SENDBIRD_API_TOKEN", "YOUR_API_TOKEN")

    # AI Assistant 설정
    AI_USER_ID: str = "home_ai_assistant"
    AI_USER_NAME: str = "My Home"
    AI_PROFILE_URL: str = ""

    # API Endpoints
    CHAT_API_BASE: str = f"https://api-{APP_ID}.sendbird.com/v3"
    CALLS_API_BASE: str = f"https://api-{APP_ID}.calls.sendbird.com/v1"

    # Geofence 설정
    HOME_LATITUDE: float = float(os.getenv("HOME_LATITUDE", "37.5665"))
    HOME_LONGITUDE: float = float(os.getenv("HOME_LONGITUDE", "126.9780"))
    GEOFENCE_RADIUS_METERS: float = float(os.getenv("GEOFENCE_RADIUS", "100.0"))

    @classmethod
    def get_chat_headers(cls) -> dict:
        """Chat API 헤더"""
        return {"Content-Type": "application/json", "Api-Token": cls.API_TOKEN}

    @classmethod
    def get_calls_headers(cls) -> dict:
        """Calls API 헤더"""
        return {"Content-Type": "application/json", "Api-Token": cls.API_TOKEN}

    @classmethod
    def get_channel_url(cls, user_id: str) -> str:
        """채널 URL 생성"""
        return f"chat_{user_id}_{cls.AI_USER_ID}"

