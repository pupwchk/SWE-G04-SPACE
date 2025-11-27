#!/usr/bin/env python3
"""
가전 규칙 수정 API 테스트
"""
import requests
import json
import os

BASE_URL = "http://localhost:11325/api"

# User ID 읽기
if os.path.exists("test_user_id.txt"):
    with open("test_user_id.txt", "r") as f:
        USER_ID = f.read().strip()
else:
    print("❌ test_user_id.txt 파일이 없습니다. create_test_user.py를 먼저 실행하세요.")
    exit(1)

print("=" * 60)
print("가전 규칙 수정 API 테스트")
print("=" * 60)
print(f"User ID: {USER_ID}\n")

# 1. 현재 규칙 조회
print("1️⃣ 제습기 규칙 조회 (수정 전)")
print("-" * 60)
try:
    response = requests.get(
        f"{BASE_URL}/appliances/rules/{USER_ID}",
        params={"appliance_type": "제습기"},
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        rules = data.get("rules", [])
        print(f"✅ 제습기 규칙 {len(rules)}개")
        for rule in rules:
            print(f"   피로도 {rule['fatigue_level']}: "
                  f"조건={rule['condition']}, "
                  f"활성화={rule['is_enabled']}")
    else:
        print(f"❌ 에러: {response.status_code}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 2. 제습기 자동 작동 비활성화
print("\n2️⃣ 제습기 자동 작동 비활성화")
print("-" * 60)
try:
    response = requests.patch(
        f"{BASE_URL}/appliances/rules/{USER_ID}",
        json={
            "appliance_type": "제습기",
            "operation": "disable"
        },
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message')}")
        print(f"   업데이트된 규칙: {data.get('updated_count')}개")
    else:
        print(f"❌ 에러: {response.status_code} - {response.text[:200]}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 3. 비활성화 확인
print("\n3️⃣ 제습기 규칙 조회 (비활성화 확인)")
print("-" * 60)
try:
    response = requests.get(
        f"{BASE_URL}/appliances/rules/{USER_ID}",
        params={"appliance_type": "제습기"},
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        rules = data.get("rules", [])
        all_disabled = all(not rule['is_enabled'] for rule in rules)
        if all_disabled:
            print(f"✅ 모든 제습기 규칙이 비활성화됨 ({len(rules)}개)")
        else:
            print(f"⚠️ 일부 규칙이 여전히 활성화 상태")
    else:
        print(f"❌ 에러: {response.status_code}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 4. 가전 추천 (제습기 제외되어야 함)
print("\n4️⃣ 가전 추천 API (제습기가 제외되어야 함)")
print("-" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/appliances/recommend/{USER_ID}",
        json={
            "latitude": 37.5665,
            "longitude": 126.9780,
            "sido": "서울"
        },
        timeout=15
    )
    if response.status_code == 200:
        data = response.json()
        recs = data.get("recommendations", [])
        has_dehumidifier = any(rec['appliance_type'] == '제습기' for rec in recs)

        print(f"✅ 추천: {len(recs)}개 가전")
        for rec in recs:
            print(f"   - {rec.get('appliance_type')}: {rec.get('action')}")

        if has_dehumidifier:
            print(f"❌ 제습기가 여전히 추천에 포함됨!")
        else:
            print(f"✅ 제습기가 추천에서 제외됨")
    else:
        print(f"❌ 에러: {response.status_code}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 5. 제습기 다시 활성화
print("\n5️⃣ 제습기 자동 작동 다시 활성화")
print("-" * 60)
try:
    response = requests.patch(
        f"{BASE_URL}/appliances/rules/{USER_ID}",
        json={
            "appliance_type": "제습기",
            "operation": "enable"
        },
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message')}")
    else:
        print(f"❌ 에러: {response.status_code}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 6. 에어컨 임계값 수정
print("\n6️⃣ 에어컨 온도 임계값 수정 (28°C → 26°C)")
print("-" * 60)
try:
    response = requests.patch(
        f"{BASE_URL}/appliances/rules/{USER_ID}",
        json={
            "appliance_type": "에어컨",
            "operation": "modify_threshold",
            "new_threshold": {"temp_threshold": 26}
        },
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message')}")
        print(f"   새로운 임계값: {data.get('new_threshold')}")
    else:
        print(f"❌ 에러: {response.status_code} - {response.text[:200]}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 7. 수정된 에어컨 규칙 확인
print("\n7️⃣ 에어컨 규칙 조회 (임계값 확인)")
print("-" * 60)
try:
    response = requests.get(
        f"{BASE_URL}/appliances/rules/{USER_ID}",
        params={"appliance_type": "에어컨"},
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        rules = data.get("rules", [])
        print(f"✅ 에어컨 규칙 {len(rules)}개")
        for rule in rules:
            print(f"   피로도 {rule['fatigue_level']}: "
                  f"임계값={rule['condition'].get('temp_threshold')}°C")
    else:
        print(f"❌ 에러: {response.status_code}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

print("\n" + "=" * 60)
print("테스트 완료!")
print("=" * 60)
