#!/usr/bin/env python3
"""
시연용 가전 더미 데이터 생성 스크립트
djwnsgh0248@gmail.com 사용자를 위한 LG 가전 5종 생성
"""
import sys
import os
from uuid import UUID

# Python 경로에 현재 디렉토리 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.db import SessionLocal
from app.models.user import User
from app.models.info import (
    Appliance,
    AirConditionerConfig,
    TvConfig,
    AirPurifierConfig,
    LightConfig,
    HumidifierConfig,
)
from app.models.appliance import ApplianceConditionRule


def get_user_by_email(db, email: str):
    """이메일로 사용자 조회"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError(f"❌ User not found: {email}")
    return user


def create_air_conditioner(db, user_id: UUID):
    """LG 에어컨 생성"""
    print("  📡 Creating LG 에어컨...")

    # 기존 에어컨 삭제 (재실행 대비)
    db.query(Appliance).filter(
        Appliance.user_id == user_id,
        Appliance.appliance_code == "AC"
    ).delete()

    appliance = Appliance(
        user_id=user_id,
        appliance_code="AC",
        display_name="거실 에어컨",
        vendor="LG",
        model_name="LG DUALCOOL WiFi",
        connection_type="wifi",
        status="ONLINE",
    )
    db.add(appliance)
    db.flush()  # ID 생성

    config = AirConditionerConfig(
        appliance_id=appliance.id,
        power_state="OFF",
        mode="cool",
        target_temp_c=24.0,
        fan_speed="auto",
        swing_mode="both",
        target_humidity_pct=50.0,
    )
    db.add(config)
    print(f"    ✅ {appliance.display_name} ({appliance.model_name}) - {appliance.status}")
    return appliance


def create_tv(db, user_id: UUID):
    """LG TV 생성"""
    print("  📺 Creating LG TV...")

    # 기존 TV 삭제
    db.query(Appliance).filter(
        Appliance.user_id == user_id,
        Appliance.appliance_code == "TV"
    ).delete()

    appliance = Appliance(
        user_id=user_id,
        appliance_code="TV",
        display_name="거실 TV",
        vendor="LG",
        model_name="OLED evo C3 65",
        connection_type="wifi",
        status="ONLINE",
    )
    db.add(appliance)
    db.flush()

    config = TvConfig(
        appliance_id=appliance.id,
        power_state="OFF",
        volume=20,
        channel=11,
        input_source="HDMI1",
        brightness=50,
        contrast=50,
        color=50,
    )
    db.add(config)
    print(f"    ✅ {appliance.display_name} ({appliance.model_name}) - {appliance.status}")
    return appliance


def create_air_purifier(db, user_id: UUID):
    """LG 공기청정기 생성"""
    print("  🌬️  Creating LG 공기청정기...")

    # 기존 공기청정기 삭제
    db.query(Appliance).filter(
        Appliance.user_id == user_id,
        Appliance.appliance_code == "AIR_PURIFIER"
    ).delete()

    appliance = Appliance(
        user_id=user_id,
        appliance_code="AIR_PURIFIER",
        display_name="거실 공기청정기",
        vendor="LG",
        model_name="LG PuriCare 360°",
        connection_type="wifi",
        status="ONLINE",
    )
    db.add(appliance)
    db.flush()

    config = AirPurifierConfig(
        appliance_id=appliance.id,
        power_state="OFF",
        mode="auto",
        fan_speed="auto",
        ionizer_on=True,
        target_pm10=30,
        target_pm2_5=15,
    )
    db.add(config)
    print(f"    ✅ {appliance.display_name} ({appliance.model_name}) - {appliance.status}")
    return appliance


def create_light(db, user_id: UUID):
    """LG 조명 생성"""
    print("  💡 Creating LG 조명...")

    # 기존 조명 삭제
    db.query(Appliance).filter(
        Appliance.user_id == user_id,
        Appliance.appliance_code == "LIGHT"
    ).delete()

    appliance = Appliance(
        user_id=user_id,
        appliance_code="LIGHT",
        display_name="거실 조명",
        vendor="LG",
        model_name="LG objet collection 조명",
        connection_type="wifi",
        status="ONLINE",
    )
    db.add(appliance)
    db.flush()

    config = LightConfig(
        appliance_id=appliance.id,
        power_state="OFF",
        brightness_pct=80,
        color_temperature_k=4000,
        color_hex="#FFFFFF",
        scene="reading",
    )
    db.add(config)
    print(f"    ✅ {appliance.display_name} ({appliance.model_name}) - {appliance.status}")
    return appliance


def create_humidifier(db, user_id: UUID):
    """LG 가습기 생성"""
    print("  💧 Creating LG 가습기...")

    # 기존 가습기 삭제
    db.query(Appliance).filter(
        Appliance.user_id == user_id,
        Appliance.appliance_code == "HUMIDIFIER"
    ).delete()

    appliance = Appliance(
        user_id=user_id,
        appliance_code="HUMIDIFIER",
        display_name="침실 가습기",
        vendor="LG",
        model_name="LG 퓨리케어 가습기",
        connection_type="wifi",
        status="ONLINE",
    )
    db.add(appliance)
    db.flush()

    config = HumidifierConfig(
        appliance_id=appliance.id,
        power_state="OFF",
        mode="auto",
        mist_level=3,
        target_humidity_pct=50,
        warm_mist=False,
    )
    db.add(config)
    print(f"    ✅ {appliance.display_name} ({appliance.model_name}) - {appliance.status}")
    return appliance


def setup_automation_rules(db, user_id: UUID):
    """자동화 규칙 생성 (피로도 레벨별)"""
    print("\n🔧 Creating automation rules...")

    # 기존 규칙 삭제
    db.query(ApplianceConditionRule).filter(
        ApplianceConditionRule.user_id == user_id
    ).delete()

    rules = [
        # ===== 피로도 1 (좋음) =====
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="에어컨",
            action="on",
            condition_json={"temp_threshold": 28, "operator": ">="},
            settings_json={"target_temp_c": 24, "fan_speed": "auto"},
            fatigue_level=1,
            priority=1,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="제습기",
            action="on",
            condition_json={"humidity_threshold": 70, "operator": ">="},
            settings_json={"target_humidity_pct": 50},
            fatigue_level=1,
            priority=2,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="공기청정기",
            action="on",
            condition_json={"pm10_threshold": 50, "operator": ">="},
            settings_json={"mode": "auto", "fan_speed": "auto"},
            fatigue_level=1,
            priority=3,
            is_enabled=True
        ),

        # ===== 피로도 2 (보통) =====
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="에어컨",
            action="on",
            condition_json={"temp_threshold": 26, "operator": ">="},
            settings_json={"target_temp_c": 23, "fan_speed": "mid"},
            fatigue_level=2,
            priority=1,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="제습기",
            action="on",
            condition_json={"humidity_threshold": 65, "operator": ">="},
            settings_json={"target_humidity_pct": 50},
            fatigue_level=2,
            priority=2,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="공기청정기",
            action="on",
            condition_json={"pm10_threshold": 40, "operator": ">="},
            settings_json={"mode": "auto", "fan_speed": "mid"},
            fatigue_level=2,
            priority=3,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="가습기",
            action="on",
            condition_json={"humidity_threshold": 35, "operator": "<="},
            settings_json={"target_humidity_pct": 50, "mode": "auto"},
            fatigue_level=2,
            priority=4,
            is_enabled=True
        ),

        # ===== 피로도 3 (피곤함) =====
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="에어컨",
            action="on",
            condition_json={"temp_threshold": 25, "operator": ">="},
            settings_json={"target_temp_c": 22, "fan_speed": "mid"},
            fatigue_level=3,
            priority=1,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="제습기",
            action="on",
            condition_json={"humidity_threshold": 60, "operator": ">="},
            settings_json={"target_humidity_pct": 45},
            fatigue_level=3,
            priority=2,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="공기청정기",
            action="on",
            condition_json={"pm10_threshold": 30, "operator": ">="},
            settings_json={"mode": "turbo", "fan_speed": "high"},
            fatigue_level=3,
            priority=3,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="가습기",
            action="on",
            condition_json={"humidity_threshold": 40, "operator": "<="},
            settings_json={"target_humidity_pct": 55, "mode": "auto"},
            fatigue_level=3,
            priority=4,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="조명",
            action="on",
            condition_json={},  # 무조건 켜기
            settings_json={"brightness_pct": 60, "scene": "relax"},
            fatigue_level=3,
            priority=5,
            is_enabled=True
        ),

        # ===== 피로도 4 (매우 피곤함) =====
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="에어컨",
            action="on",
            condition_json={"temp_threshold": 24, "operator": ">="},
            settings_json={"target_temp_c": 21, "fan_speed": "low"},
            fatigue_level=4,
            priority=1,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="제습기",
            action="on",
            condition_json={"humidity_threshold": 55, "operator": ">="},
            settings_json={"target_humidity_pct": 45},
            fatigue_level=4,
            priority=2,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="공기청정기",
            action="on",
            condition_json={"pm10_threshold": 25, "operator": ">="},
            settings_json={"mode": "turbo", "fan_speed": "high"},
            fatigue_level=4,
            priority=3,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="가습기",
            action="on",
            condition_json={"humidity_threshold": 45, "operator": "<="},
            settings_json={"target_humidity_pct": 60, "mode": "auto", "warm_mist": True},
            fatigue_level=4,
            priority=4,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="조명",
            action="on",
            condition_json={},  # 무조건 켜기
            settings_json={"brightness_pct": 40, "scene": "sleep"},
            fatigue_level=4,
            priority=5,
            is_enabled=True
        ),
        ApplianceConditionRule(
            user_id=user_id,
            appliance_type="커튼",
            action="on",
            condition_json={},  # 무조건 켜기 (닫기)
            settings_json={"position": "closed"},
            fatigue_level=4,
            priority=6,
            is_enabled=True
        ),
    ]

    for rule in rules:
        db.add(rule)

    print(f"  ✅ {len(rules)} automation rules created (Fatigue levels 1-4)")


def main():
    """메인 함수"""
    TARGET_EMAIL = "djwnsgh0248@gmail.com"

    print("=" * 60)
    print("🏠 시연용 LG 가전 더미 데이터 생성 스크립트")
    print("=" * 60)
    print()

    db = SessionLocal()

    try:
        # 1. 사용자 조회
        print(f"🔍 Looking for user: {TARGET_EMAIL}")
        user = get_user_by_email(db, TARGET_EMAIL)
        print(f"✅ Found user: {user.id}")
        print()

        # 2. 가전 생성
        print("🏠 Creating LG ThinQ appliances...")
        create_air_conditioner(db, user.id)
        create_tv(db, user.id)
        create_air_purifier(db, user.id)
        create_light(db, user.id)
        create_humidifier(db, user.id)

        # 3. 자동화 규칙 생성
        setup_automation_rules(db, user.id)

        # 4. 커밋
        db.commit()

        print()
        print("=" * 60)
        print("✅ Demo appliances created successfully!")
        print("=" * 60)
        print()
        print("📋 Summary:")
        print(f"  - User: {TARGET_EMAIL}")
        print(f"  - User ID: {user.id}")
        print(f"  - Appliances: 5 (All LG ThinQ)")
        print(f"  - Automation Rules: 27 (Fatigue levels 1-4)")
        print()
        print("🧪 Test with:")
        print(f"  curl http://localhost/api/appliances/user/{user.id}")
        print(f"  curl http://localhost/api/appliances/smart-status/{user.id}")
        print(f"  curl http://localhost/api/appliances/rules/{user.id}")
        print()

    except ValueError as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        print("\n💡 Tip: Make sure the user exists in the database first.")
        sys.exit(1)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
