"""
가전 타입 매핑 및 설정 유틸리티
프론트엔드 포맷과 백엔드 데이터를 매핑
"""
from typing import Dict, Any, Optional


# 가전 타입 매핑: 한글 표시 이름 -> 백엔드 코드
APPLIANCE_TYPE_MAPPING = {
    "에어컨": "AC",
    "조명": "LIGHT",
    "공기청정기": "AIR_PURIFIER",
    "제습기": "DEHUMIDIFIER",
    "가습기": "HUMIDIFIER",
    "TV": "TV"
}

# 역방향 매핑: 백엔드 코드 -> 한글 표시 이름
BACKEND_CODE_TO_DISPLAY = {
    "AC": "에어컨",
    "LIGHT": "조명",
    "AIR_PURIFIER": "공기청정기",
    "DEHUMIDIFIER": "제습기",
    "HUMIDIFIER": "가습기",
    "TV": "TV"
}


def get_backend_code(display_name: str) -> str:
    """
    한글 표시 이름을 백엔드 코드로 변환

    Args:
        display_name: 한글 표시 이름 (예: "에어컨")

    Returns:
        백엔드 코드 (예: "AC")
    """
    return APPLIANCE_TYPE_MAPPING.get(display_name, display_name)


def get_display_name(backend_code: str) -> str:
    """
    백엔드 코드를 한글 표시 이름으로 변환

    Args:
        backend_code: 백엔드 코드 (예: "AC")

    Returns:
        한글 표시 이름 (예: "에어컨")
    """
    return BACKEND_CODE_TO_DISPLAY.get(backend_code, backend_code)


def format_settings_for_frontend(
    appliance_type: str,
    settings: Dict[str, Any]
) -> Dict[str, Any]:
    """
    백엔드 설정을 프론트엔드 포맷으로 변환

    Args:
        appliance_type: 가전 종류 (한글)
        settings: 백엔드 설정값

    Returns:
        프론트엔드 포맷 설정값
    """
    if not settings:
        return {}

    # 각 가전 타입별로 필요한 필드 매핑
    formatted = {}

    if appliance_type == "에어컨":
        # power_state는 is_on으로 판단
        formatted["mode"] = settings.get("mode", "냉방")
        formatted["target_temp_c"] = settings.get("target_temp_c", 23)
        formatted["fan_speed"] = settings.get("fan_speed", 3)

    elif appliance_type == "조명":
        formatted["scene"] = settings.get("scene")
        formatted["brightness_pct"] = settings.get("brightness_pct", 100)
        formatted["color_temperature_k"] = settings.get("color_temperature_k")
        formatted["color_hex"] = settings.get("color_hex")

    elif appliance_type == "공기청정기":
        formatted["mode"] = settings.get("mode", "자동")
        formatted["fan_speed"] = settings.get("fan_speed", 3)
        formatted["target_pm2_5"] = settings.get("target_pm2_5")
        formatted["target_pm10"] = settings.get("target_pm10")
        formatted["ionizer_on"] = settings.get("ionizer_on")

    elif appliance_type == "제습기":
        formatted["mode"] = settings.get("mode", "일반")
        formatted["target_humidity_pct"] = settings.get("target_humidity_pct", 45)
        formatted["fan_speed"] = settings.get("fan_speed", 2)

    elif appliance_type == "가습기":
        formatted["mode"] = settings.get("mode", "자동")
        formatted["target_humidity_pct"] = settings.get("target_humidity_pct", 50)
        formatted["mist_level"] = settings.get("mist_level", 2)
        formatted["warm_mist"] = settings.get("warm_mist")

    elif appliance_type == "TV":
        formatted["input_source"] = settings.get("input_source", "OTT")
        formatted["volume"] = settings.get("volume", 30)
        formatted["brightness"] = settings.get("brightness", 70)
        formatted["channel"] = settings.get("channel")
        formatted["contrast"] = settings.get("contrast")
        formatted["color"] = settings.get("color")

    return formatted


def format_appliance_status_for_frontend(
    appliance_type: str,
    is_on: bool,
    current_settings: Optional[Dict[str, Any]],
    last_command: Optional[Dict[str, Any]],
    last_updated: str
) -> Dict[str, Any]:
    """
    백엔드 가전 상태를 프론트엔드 포맷으로 변환

    Args:
        appliance_type: 가전 종류 (한글)
        is_on: 전원 상태
        current_settings: 현재 설정값
        last_command: 마지막 명령
        last_updated: 마지막 업데이트 시간

    Returns:
        프론트엔드 포맷 가전 상태
    """
    return {
        "appliance_type": appliance_type,
        "is_on": is_on,
        "current_settings": format_settings_for_frontend(
            appliance_type, current_settings or {}
        ),
        "last_command": last_command,
        "last_updated": last_updated
    }


def validate_settings(
    appliance_type: str,
    settings: Dict[str, Any]
) -> tuple[bool, Optional[str]]:
    """
    설정값 유효성 검증

    Args:
        appliance_type: 가전 종류 (한글)
        settings: 검증할 설정값

    Returns:
        (유효성 여부, 에러 메시지)
    """
    if appliance_type == "에어컨":
        if "target_temp_c" in settings:
            temp = settings["target_temp_c"]
            if not (18 <= temp <= 28):
                return False, "에어컨 온도는 18-28도 사이여야 합니다"

        if "fan_speed" in settings:
            speed = settings["fan_speed"]
            if not (1 <= speed <= 5):
                return False, "에어컨 풍속은 1-5단 사이여야 합니다"

        if "mode" in settings:
            valid_modes = ["냉방", "제습", "송풍", "자동", "난방"]
            if settings["mode"] not in valid_modes:
                return False, f"에어컨 모드는 {valid_modes} 중 하나여야 합니다"

    elif appliance_type == "조명":
        if "brightness_pct" in settings:
            brightness = settings["brightness_pct"]
            if not (0 <= brightness <= 100):
                return False, "조명 밝기는 0-100% 사이여야 합니다"

        if "color_temperature_k" in settings:
            temp = settings["color_temperature_k"]
            if not (2700 <= temp <= 6500):
                return False, "색온도는 2700-6500K 사이여야 합니다"

    elif appliance_type == "공기청정기":
        if "fan_speed" in settings:
            speed = settings["fan_speed"]
            if not (1 <= speed <= 5):
                return False, "공기청정기 풍속은 1-5단 사이여야 합니다"

    elif appliance_type == "제습기":
        if "target_humidity_pct" in settings:
            humidity = settings["target_humidity_pct"]
            if not (35 <= humidity <= 60):
                return False, "제습기 목표 습도는 35-60% 사이여야 합니다"

        if "fan_speed" in settings:
            speed = settings["fan_speed"]
            if not (1 <= speed <= 4):
                return False, "제습기 풍속은 1-4단 사이여야 합니다"

    elif appliance_type == "가습기":
        if "target_humidity_pct" in settings:
            humidity = settings["target_humidity_pct"]
            if not (40 <= humidity <= 65):
                return False, "가습기 목표 습도는 40-65% 사이여야 합니다"

        if "mist_level" in settings:
            level = settings["mist_level"]
            if not (1 <= level <= 4):
                return False, "가습기 분무량은 1-4단 사이여야 합니다"

    elif appliance_type == "TV":
        if "volume" in settings:
            volume = settings["volume"]
            if not (0 <= volume <= 100):
                return False, "TV 볼륨은 0-100 사이여야 합니다"

        if "brightness" in settings:
            brightness = settings["brightness"]
            if not (30 <= brightness <= 100):
                return False, "TV 밝기는 30-100% 사이여야 합니다"

    return True, None
