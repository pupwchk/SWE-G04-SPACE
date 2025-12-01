"""
가전 작동 조건 룰 엔진
피로도 + 날씨 조건에 따라 가전 제어 결정
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.appliance import ApplianceConditionRule, UserAppliancePreference
from app.services.hrv_service import hrv_service
from app.services.weather_service import weather_service

logger = logging.getLogger(__name__)


class ApplianceRuleEngine:
    """가전 작동 조건 평가 엔진"""

    @staticmethod
    def evaluate_condition(
        condition: Dict[str, Any],
        weather_data: Dict[str, Any]
    ) -> bool:
        """
        단일 조건 평가

        Args:
            condition: 조건 JSON (예: {"temp_threshold": 28, "operator": ">="})
            weather_data: 날씨 데이터

        Returns:
            조건 만족 여부
        """
        # 온도 조건
        if "temp_threshold" in condition:
            temp = weather_data.get("temperature")
            if temp is None:
                return False

            threshold = condition["temp_threshold"]
            operator = condition.get("operator", ">=")

            if operator == ">=":
                return temp >= threshold
            elif operator == "<=":
                return temp <= threshold
            elif operator == ">":
                return temp > threshold
            elif operator == "<":
                return temp < threshold
            elif operator == "==":
                return abs(temp - threshold) < 0.5

        # 습도 조건
        if "humidity_threshold" in condition:
            humidity = weather_data.get("humidity")
            if humidity is None:
                return False

            threshold = condition["humidity_threshold"]
            operator = condition.get("operator", ">=")

            if operator == ">=":
                return humidity >= threshold
            elif operator == "<=":
                return humidity <= threshold
            elif operator == ">":
                return humidity > threshold
            elif operator == "<":
                return humidity < threshold

        # 미세먼지 조건
        if "pm10_threshold" in condition:
            pm10 = weather_data.get("pm10")
            if pm10 is None:
                return False

            threshold = condition["pm10_threshold"]
            operator = condition.get("operator", ">=")

            if operator == ">=":
                return pm10 >= threshold
            elif operator == "<=":
                return pm10 <= threshold

        # 초미세먼지 조건
        if "pm2_5_threshold" in condition:
            pm2_5 = weather_data.get("pm2_5")
            if pm2_5 is None:
                return False

            threshold = condition["pm2_5_threshold"]
            operator = condition.get("operator", ">=")

            if operator == ">=":
                return pm2_5 >= threshold
            elif operator == "<=":
                return pm2_5 <= threshold

        # 조건 없음 (항상 true)
        return True

    @staticmethod
    def get_appliances_to_control(
        db: Session,
        user_id: str,
        weather_data: Dict[str, Any],
        fatigue_level: Optional[int] = None
    ) -> list[Dict[str, Any]]:
        """
        제어할 가전 목록 결정

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            weather_data: 날씨 데이터
            fatigue_level: 피로도 레벨 (None이면 최신 HRV 조회)

        Returns:
            제어할 가전 정보 리스트
            [
                {
                    "appliance_type": "에어컨",
                    "action": "on",
                    "settings": {"target_temp_c": 25, ...},
                    "reason": "온도가 28도 이상입니다"
                },
                ...
            ]
        """
        # 피로도 조회
        if fatigue_level is None:
            fatigue_level = hrv_service.get_latest_fatigue_level(db, user_id)

        if fatigue_level is None:
            logger.warning(f"⚠️ No fatigue level for user {user_id}, using default level 2")
            fatigue_level = 2

        logger.info(f"🔧 Evaluating appliance rules for user={user_id}, fatigue={fatigue_level}")

        # 해당 피로도 레벨의 활성화된 규칙 조회
        rules = db.query(ApplianceConditionRule)\
            .filter(
                ApplianceConditionRule.user_id == user_id,
                ApplianceConditionRule.fatigue_level == fatigue_level,
                ApplianceConditionRule.is_enabled == True
            )\
            .all()

        if not rules:
            logger.info(f"ℹ️ No active rules for user {user_id} at fatigue level {fatigue_level}")
            return []

        # 조건 평가
        appliances_to_control = []

        for rule in rules:
            condition_met = ApplianceRuleEngine.evaluate_condition(
                rule.condition_json,
                weather_data
            )

            if condition_met:
                # 📚 우선순위: UserAppliancePreference > ApplianceConditionRule.settings_json
                # 사용자가 학습한 선호 세팅이 있는지 먼저 확인
                preference = db.query(UserAppliancePreference).filter(
                    UserAppliancePreference.user_id == UUID(user_id),
                    UserAppliancePreference.fatigue_level == fatigue_level,
                    UserAppliancePreference.appliance_type == rule.appliance_type
                ).first()

                if preference:
                    # 학습된 선호 세팅 사용
                    settings_json = preference.settings_json

                    # 에어컨의 경우 냉방/난방 모드 선택
                    if rule.appliance_type == "에어컨" and isinstance(settings_json, dict):
                        mode = rule.condition_json.get("mode", "cool")
                        if mode in settings_json:
                            settings = settings_json[mode]
                        else:
                            # cool/heat 중 하나만 있거나 직접 설정인 경우
                            settings = settings_json
                    else:
                        settings = settings_json

                    logger.info(f"📚 Using learned preference for {rule.appliance_type} at fatigue {fatigue_level}")
                else:
                    # 기본 규칙 세팅 사용
                    settings = rule.settings_json or {}
                    logger.info(f"📋 Using default rule settings for {rule.appliance_type}")

                # 제어 정보 생성
                control_info = {
                    "appliance_type": rule.appliance_type,
                    "action": rule.action,
                    "settings": settings,
                    "reason": ApplianceRuleEngine._generate_reason(
                        rule.appliance_type,
                        rule.condition_json,
                        weather_data
                    ),
                    "fatigue_level": fatigue_level,
                    "priority": rule.priority
                }

                appliances_to_control.append(control_info)
                logger.info(f"✅ {rule.appliance_type} should be {rule.action}: {rule.condition_json}")

        return appliances_to_control

    @staticmethod
    def _generate_reason(
        appliance_type: str,
        condition: Dict[str, Any],
        weather_data: Dict[str, Any]
    ) -> str:
        """
        제어 이유 생성

        Args:
            appliance_type: 가전 종류
            condition: 조건
            weather_data: 날씨 데이터

        Returns:
            이유 텍스트
        """
        reasons = []

        if "temp_threshold" in condition:
            temp = weather_data.get("temperature")
            if temp is not None:
                reasons.append(f"온도가 {temp:.1f}°C입니다")

        if "humidity_threshold" in condition:
            humidity = weather_data.get("humidity")
            if humidity is not None:
                reasons.append(f"습도가 {humidity:.1f}%입니다")

        if "pm10_threshold" in condition:
            pm10 = weather_data.get("pm10")
            if pm10 is not None:
                reasons.append(f"미세먼지(PM10)가 {pm10:.1f}㎍/㎥입니다")

        if "pm2_5_threshold" in condition:
            pm2_5 = weather_data.get("pm2_5")
            if pm2_5 is not None:
                reasons.append(f"초미세먼지(PM2.5)가 {pm2_5:.1f}㎍/㎥입니다")

        if not reasons:
            return f"{appliance_type} 작동 조건이 만족되었습니다"

        return ", ".join(reasons)

    @staticmethod
    def create_default_rules(db: Session, user_id: str):
        """
        사용자를 위한 기본 규칙 생성

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
        """
        # 기존 규칙 확인
        existing = db.query(ApplianceConditionRule)\
            .filter(ApplianceConditionRule.user_id == user_id)\
            .first()

        if existing:
            logger.info(f"ℹ️ User {user_id} already has rules")
            return

        logger.info(f"📝 Creating default rules for user {user_id}")

        # 피로도별 기본 규칙 정의
        default_rules = [
            # 피로도 1 (좋음)
            {
                "fatigue_level": 1,
                "appliance_type": "에어컨",
                "action": "on",
                "condition_json": {"temp_threshold": 28, "operator": ">=", "mode": "cool"}
            },
            {
                "fatigue_level": 1,
                "appliance_type": "에어컨",
                "action": "on",
                "condition_json": {"temp_threshold": 10, "operator": "<=", "mode": "heat"}
            },
            {
                "fatigue_level": 1,
                "appliance_type": "가습기",
                "action": "on",
                "condition_json": {"humidity_threshold": 30, "operator": "<="}
            },
            {
                "fatigue_level": 1,
                "appliance_type": "제습기",
                "action": "on",
                "condition_json": {"humidity_threshold": 70, "operator": ">="}
            },
            {
                "fatigue_level": 1,
                "appliance_type": "공기청정기",
                "action": "on",
                "condition_json": {"pm10_threshold": 50, "operator": ">="}
            },

            # 피로도 2 (보통) - 약간 낮은 기준
            {
                "fatigue_level": 2,
                "appliance_type": "에어컨",
                "action": "on",
                "condition_json": {"temp_threshold": 27, "operator": ">=", "mode": "cool"}
            },
            {
                "fatigue_level": 2,
                "appliance_type": "에어컨",
                "action": "on",
                "condition_json": {"temp_threshold": 10, "operator": "<=", "mode": "heat"}
            },
            {
                "fatigue_level": 2,
                "appliance_type": "가습기",
                "action": "on",
                "condition_json": {"humidity_threshold": 35, "operator": "<="}
            },
            {
                "fatigue_level": 2,
                "appliance_type": "제습기",
                "action": "on",
                "condition_json": {"humidity_threshold": 65, "operator": ">="}
            },
            {
                "fatigue_level": 2,
                "appliance_type": "공기청정기",
                "action": "on",
                "condition_json": {"pm10_threshold": 40, "operator": ">="}
            },

            # 피로도 3 (나쁨) - 더 낮은 기준
            {
                "fatigue_level": 3,
                "appliance_type": "에어컨",
                "action": "on",
                "condition_json": {"temp_threshold": 26, "operator": ">=", "mode": "cool"}
            },
            {
                "fatigue_level": 3,
                "appliance_type": "에어컨",
                "action": "on",
                "condition_json": {"temp_threshold": 10, "operator": "<=", "mode": "heat"}
            },
            {
                "fatigue_level": 3,
                "appliance_type": "가습기",
                "action": "on",
                "condition_json": {"humidity_threshold": 40, "operator": "<="}
            },
            {
                "fatigue_level": 3,
                "appliance_type": "제습기",
                "action": "on",
                "condition_json": {"humidity_threshold": 60, "operator": ">="}
            },
            {
                "fatigue_level": 3,
                "appliance_type": "공기청정기",
                "action": "on",
                "condition_json": {"pm10_threshold": 30, "operator": ">="}
            },
            {
                "fatigue_level": 3,
                "appliance_type": "조명",
                "action": "on",
                "condition_json": {}  # 항상 켜기
            },

            # 피로도 4 (매우 나쁨) - 가장 낮은 기준
            {
                "fatigue_level": 4,
                "appliance_type": "에어컨",
                "action": "on",
                "condition_json": {"temp_threshold": 25, "operator": ">=", "mode": "cool"}
            },
            {
                "fatigue_level": 4,
                "appliance_type": "에어컨",
                "action": "on",
                "condition_json": {"temp_threshold": 10, "operator": "<=", "mode": "heat"}
            },
            {
                "fatigue_level": 4,
                "appliance_type": "가습기",
                "action": "on",
                "condition_json": {"humidity_threshold": 45, "operator": "<="}
            },
            {
                "fatigue_level": 4,
                "appliance_type": "제습기",
                "action": "on",
                "condition_json": {"humidity_threshold": 55, "operator": ">="}
            },
            {
                "fatigue_level": 4,
                "appliance_type": "공기청정기",
                "action": "on",
                "condition_json": {"pm10_threshold": 20, "operator": ">="}
            },
            {
                "fatigue_level": 4,
                "appliance_type": "조명",
                "action": "on",
                "condition_json": {}  # 항상 켜기
            },
        ]

        # 피로도별 기본 선호 세팅
        # 에어컨의 경우 냉방/난방 모드를 settings_json에 포함하여 구분
        default_preferences = [
            # 피로도 1
            {"fatigue_level": 1, "appliance_type": "에어컨", "settings_json": {
                "cool": {"mode": "cool", "target_temp_c": 25, "fan_speed": "low", "swing_mode": "off"},
                "heat": {"mode": "heat", "target_temp_c": 22, "fan_speed": "low", "swing_mode": "off"}
            }},
            {"fatigue_level": 1, "appliance_type": "가습기", "settings_json": {"mode": "auto", "target_humidity_pct": 50}},
            {"fatigue_level": 1, "appliance_type": "제습기", "settings_json": {"mode": "auto", "target_humidity_pct": 50}},
            {"fatigue_level": 1, "appliance_type": "공기청정기", "settings_json": {"mode": "auto", "fan_speed": "low"}},

            # 피로도 2
            {"fatigue_level": 2, "appliance_type": "에어컨", "settings_json": {
                "cool": {"mode": "cool", "target_temp_c": 24, "fan_speed": "mid", "swing_mode": "vertical"},
                "heat": {"mode": "heat", "target_temp_c": 23, "fan_speed": "mid", "swing_mode": "vertical"}
            }},
            {"fatigue_level": 2, "appliance_type": "가습기", "settings_json": {"mode": "auto", "target_humidity_pct": 55}},
            {"fatigue_level": 2, "appliance_type": "제습기", "settings_json": {"mode": "auto", "target_humidity_pct": 45}},
            {"fatigue_level": 2, "appliance_type": "공기청정기", "settings_json": {"mode": "auto", "fan_speed": "mid"}},

            # 피로도 3
            {"fatigue_level": 3, "appliance_type": "에어컨", "settings_json": {
                "cool": {"mode": "cool", "target_temp_c": 23, "fan_speed": "mid", "swing_mode": "both"},
                "heat": {"mode": "heat", "target_temp_c": 24, "fan_speed": "high", "swing_mode": "both"}
            }},
            {"fatigue_level": 3, "appliance_type": "가습기", "settings_json": {"mode": "high", "target_humidity_pct": 60}},
            {"fatigue_level": 3, "appliance_type": "제습기", "settings_json": {"mode": "high", "target_humidity_pct": 40}},
            {"fatigue_level": 3, "appliance_type": "공기청정기", "settings_json": {"mode": "turbo", "fan_speed": "high"}},
            {"fatigue_level": 3, "appliance_type": "조명", "settings_json": {"brightness_pct": 70, "color_temp": "warm"}},

            # 피로도 4
            {"fatigue_level": 4, "appliance_type": "에어컨", "settings_json": {
                "cool": {"mode": "cool", "target_temp_c": 22, "fan_speed": "high", "swing_mode": "both"},
                "heat": {"mode": "heat", "target_temp_c": 25, "fan_speed": "high", "swing_mode": "both"}
            }},
            {"fatigue_level": 4, "appliance_type": "가습기", "settings_json": {"mode": "high", "target_humidity_pct": 60}},
            {"fatigue_level": 4, "appliance_type": "제습기", "settings_json": {"mode": "high", "target_humidity_pct": 40}},
            {"fatigue_level": 4, "appliance_type": "공기청정기", "settings_json": {"mode": "turbo", "fan_speed": "high"}},
            {"fatigue_level": 4, "appliance_type": "조명", "settings_json": {"brightness_pct": 100, "color_temp": "warm"}},
        ]

        # 규칙 생성
        for rule_data in default_rules:
            rule = ApplianceConditionRule(
                user_id=user_id,
                **rule_data
            )
            db.add(rule)

        # 선호 세팅 생성
        for pref_data in default_preferences:
            pref = UserAppliancePreference(
                user_id=user_id,
                **pref_data
            )
            db.add(pref)

        db.commit()
        logger.info(f"✅ Created {len(default_rules)} rules and {len(default_preferences)} preferences for user {user_id}")


# 싱글톤 인스턴스
appliance_rule_engine = ApplianceRuleEngine()
