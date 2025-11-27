#!/usr/bin/env python3
"""
가전 제어 규칙 초기 설정
사용자의 피로도별 가전 자동 제어 조건 생성
"""
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.db import SessionLocal
from app.models.appliance import ApplianceConditionRule

def setup_rules(user_id: str):
    """기본 가전 제어 규칙 생성"""
    db = SessionLocal()

    try:
        # 기존 규칙 삭제
        db.query(ApplianceConditionRule).filter(
            ApplianceConditionRule.user_id == user_id
        ).delete()

        rules = [
            # 피로도 1 (좋음) - 기본 규칙
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
                appliance_type="난방",
                action="on",
                condition_json={"temp_threshold": 16, "operator": "<="},
                settings_json={"target_temp_c": 22},
                fatigue_level=1,
                priority=1,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="제습기",
                action="on",
                condition_json={"humidity_threshold": 70, "operator": ">="},
                settings_json={"target_humidity": 50},
                fatigue_level=1,
                priority=2,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="공기청정기",
                action="on",
                condition_json={"pm10_threshold": 50, "operator": ">="},
                settings_json={"mode": "auto"},
                fatigue_level=1,
                priority=2,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="공기청정기",
                action="on",
                condition_json={"pm2_5_threshold": 35, "operator": ">="},
                settings_json={"mode": "turbo"},
                fatigue_level=1,
                priority=3,
                is_enabled=True
            ),

            # 피로도 2 (보통) - 조금 더 적극적
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="에어컨",
                action="on",
                condition_json={"temp_threshold": 26, "operator": ">="},
                settings_json={"target_temp_c": 23, "fan_speed": "medium"},
                fatigue_level=2,
                priority=1,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="난방",
                action="on",
                condition_json={"temp_threshold": 18, "operator": "<="},
                settings_json={"target_temp_c": 23},
                fatigue_level=2,
                priority=1,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="제습기",
                action="on",
                condition_json={"humidity_threshold": 65, "operator": ">="},
                settings_json={"target_humidity": 50},
                fatigue_level=2,
                priority=2,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="공기청정기",
                action="on",
                condition_json={"pm10_threshold": 40, "operator": ">="},
                settings_json={"mode": "auto"},
                fatigue_level=2,
                priority=2,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="조명",
                action="on",
                condition_json={},  # 항상
                settings_json={"brightness": 70, "color_temp": "warm"},
                fatigue_level=2,
                priority=3,
                is_enabled=True
            ),

            # 피로도 3 (피곤) - 더 적극적
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="에어컨",
                action="on",
                condition_json={"temp_threshold": 25, "operator": ">="},
                settings_json={"target_temp_c": 22, "fan_speed": "low"},
                fatigue_level=3,
                priority=1,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="난방",
                action="on",
                condition_json={"temp_threshold": 20, "operator": "<="},
                settings_json={"target_temp_c": 24},
                fatigue_level=3,
                priority=1,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="제습기",
                action="on",
                condition_json={"humidity_threshold": 60, "operator": ">="},
                settings_json={"target_humidity": 45},
                fatigue_level=3,
                priority=2,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="공기청정기",
                action="on",
                condition_json={"pm10_threshold": 30, "operator": ">="},
                settings_json={"mode": "turbo"},
                fatigue_level=3,
                priority=2,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="조명",
                action="on",
                condition_json={},
                settings_json={"brightness": 50, "color_temp": "warm"},
                fatigue_level=3,
                priority=3,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="커튼",
                action="close",
                condition_json={},
                settings_json={"level": 80},
                fatigue_level=3,
                priority=4,
                is_enabled=True
            ),

            # 피로도 4 (매우 피곤) - 최대 케어
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
                appliance_type="난방",
                action="on",
                condition_json={"temp_threshold": 21, "operator": "<="},
                settings_json={"target_temp_c": 25},
                fatigue_level=4,
                priority=1,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="제습기",
                action="on",
                condition_json={"humidity_threshold": 55, "operator": ">="},
                settings_json={"target_humidity": 45},
                fatigue_level=4,
                priority=2,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="공기청정기",
                action="on",
                condition_json={"pm10_threshold": 25, "operator": ">="},
                settings_json={"mode": "turbo"},
                fatigue_level=4,
                priority=2,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="조명",
                action="on",
                condition_json={},
                settings_json={"brightness": 30, "color_temp": "warm"},
                fatigue_level=4,
                priority=3,
                is_enabled=True
            ),
            ApplianceConditionRule(
                user_id=user_id,
                appliance_type="커튼",
                action="close",
                condition_json={},
                settings_json={"level": 100},
                fatigue_level=4,
                priority=4,
                is_enabled=True
            ),
        ]

        db.add_all(rules)
        db.commit()

        print(f"✅ {len(rules)}개의 가전 제어 규칙이 생성되었습니다.")
        print(f"   사용자 ID: {user_id}")

        return len(rules)

    except Exception as e:
        print(f"❌ 규칙 생성 실패: {str(e)}")
        db.rollback()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    # test_user_id.txt에서 UUID 읽기
    if os.path.exists("test_user_id.txt"):
        with open("test_user_id.txt", "r") as f:
            user_id = f.read().strip()
    else:
        print("❌ test_user_id.txt 파일이 없습니다.")
        print("   create_test_user.py를 먼저 실행하세요.")
        sys.exit(1)

    print(f"🔧 가전 제어 규칙 설정 중...")
    print(f"   사용자 ID: {user_id}")
    print()

    count = setup_rules(user_id)

    if count > 0:
        print()
        print("✅ 설정 완료!")
        print()
        print("📋 생성된 규칙 예시:")
        print("   - 피로도 1: 온도 28°C 이상 → 에어컨 켜기")
        print("   - 피로도 1: 습도 70% 이상 → 제습기 켜기")
        print("   - 피로도 2: 온도 26°C 이상 → 에어컨 켜기 (더 적극적)")
        print("   - 피로도 3: 습도 60% 이상 → 제습기 켜기")
        print("   - 피로도 4: 모든 조건에서 최대 케어")
