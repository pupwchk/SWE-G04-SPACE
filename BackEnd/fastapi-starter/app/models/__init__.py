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
from app.models.tracking import (
    StressAssessment,
    FatiguePrediction,
    Place,
    TimeSlot,
    WeatherObservation,
    SleepSession,
    WorkoutSession,
    HealthHourly
)
from app.models.info import (
    Appliance,
    AirConditionerConfig,
    TvConfig,
    AirPurifierConfig,
    LightConfig,
    HumidifierConfig,
    Character
)
from app.models.chat import ChatSession, ChatMessage

__all__ = [
    # User models
    "User",
    "UserPhone",
    "UserDevice",
    # HRV models
    "HRVLog",
    "FatigueHistory",
    # Appliance rule models
    "ApplianceConditionRule",
    "UserAppliancePreference",
    "ApplianceStatus",
    "ApplianceCommandLog",
    # Weather models
    "WeatherCache",
    # Location models
    "UserLocation",
    "GeofenceTracking",
    "GeofenceEvent",
    # Tracking models
    "StressAssessment",
    "FatiguePrediction",
    "Place",
    "TimeSlot",
    "WeatherObservation",
    "SleepSession",
    "WorkoutSession",
    "HealthHourly",
    # Info models (Appliances & Character)
    "Appliance",
    "AirConditionerConfig",
    "TvConfig",
    "AirPurifierConfig",
    "LightConfig",
    "HumidifierConfig",
    "Character",
    # Chat models
    "ChatSession",
    "ChatMessage",
]
