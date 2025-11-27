# Import all models for Alembic auto-detection
from app.models.user import User, UserPhone, UserDevice
from app.models.hrv import HRVLog, FatigueHistory
from app.models.appliance import (
    ApplianceConditionRule,
    UserAppliancePreference,
    ApplianceStatus,
    ApplianceCommandLog
)
from app.models.weather import WeatherCache
from app.models.location import UserLocation, GeofenceTracking, GeofenceEvent

__all__ = [
    "User",
    "UserPhone",
    "UserDevice",
    "HRVLog",
    "FatigueHistory",
    "ApplianceConditionRule",
    "UserAppliancePreference",
    "ApplianceStatus",
    "ApplianceCommandLog",
    "WeatherCache",
    "UserLocation",
    "GeofenceTracking",
    "GeofenceEvent",
]
