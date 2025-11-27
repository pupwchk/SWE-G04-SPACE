#!/usr/bin/env python3
"""
실제 UUID 사용자로 전체 API 테스트
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
print("실제 사용자 ID로 API 테스트")
print("=" * 60)
print(f"User ID: {USER_ID}\n")

# 1. 날씨 API
print("1️⃣ 날씨 + 대기질 API")
print("-" * 60)
try:
    response = requests.get(
        f"{BASE_URL}/weather/current",
        params={"latitude": 37.5665, "longitude": 126.9780, "sido": "서울"},
        timeout=15
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 온도: {data.get('temperature')}°C")
        print(f"✅ 습도: {data.get('humidity')}%")
        print(f"✅ PM10: {data.get('pm10')} ㎍/㎥")
        print(f"✅ PM2.5: {data.get('pm2_5')} ㎍/㎥")
    else:
        print(f"❌ 에러: {response.status_code}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 2. 가전 추천 API
print("\n2️⃣ 가전 추천 API")
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
        print(f"✅ 추천: {len(recs)}개 가전")
        for rec in recs[:5]:
            print(f"   - {rec.get('appliance_type')}: {rec.get('action')} ({rec.get('reason')})")
    else:
        print(f"❌ 에러: {response.status_code} - {response.text[:200]}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 3. HRV 데이터 추가
print("\n3️⃣ HRV 데이터 추가")
print("-" * 60)
try:
    from datetime import datetime
    response = requests.post(
        f"{BASE_URL}/health/hrv",
        json={
            "user_id": USER_ID,
            "hrv_value": 45.5,
            "measured_at": datetime.now().isoformat()
        },
        timeout=10
    )
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ HRV 데이터 추가 성공")
        print(f"   피로도 레벨: {data.get('fatigue_level')}")
        print(f"   피로도 레이블: {data.get('fatigue_label')}")
    else:
        print(f"❌ 에러: {response.status_code} - {response.text[:200]}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 4. 최신 피로도 조회
print("\n4️⃣ 최신 피로도 조회")
print("-" * 60)
try:
    response = requests.get(
        f"{BASE_URL}/health/fatigue/{USER_ID}",
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 피로도 레벨: {data.get('current_fatigue_level')}")
        print(f"✅ 피로도 레이블: {data.get('fatigue_label')}")
        print(f"✅ 최신 HRV: {data.get('latest_hrv_value')}")
        print(f"✅ 7일 평균 피로도: {data.get('average_fatigue_7days')}")
    else:
        print(f"❌ 에러: {response.status_code}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 5. 가전 제어
print("\n5️⃣ 가전 직접 제어")
print("-" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/appliances/smart-control/{USER_ID}",
        json={
            "appliance_type": "에어컨",
            "action": "on",
            "settings": {"target_temp_c": 24}
        },
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 제어 성공: {data.get('status')}")
    else:
        print(f"❌ 에러: {response.status_code} - {response.text[:200]}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 6. Chat API
print("\n6️⃣ Chat API (시나리오 2)")
print("-" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/chat/{USER_ID}/message",
        json={"message": "집이 너무 덥다", "context": {}},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ AI 응답: {data.get('ai_response')}")
        print(f"✅ 의도: {data.get('intent_type')}")
        print(f"✅ 제어 필요: {data.get('needs_control')}")
        if data.get('suggestions'):
            print(f"✅ 제안: {len(data.get('suggestions'))}개")
    else:
        print(f"❌ 에러: {response.status_code}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 7. Location 업데이트 (Geofence)
print("\n7️⃣ Location 업데이트 (Geofence)")
print("-" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/location/update",
        json={
            "user_id": USER_ID,
            "latitude": 37.5665,
            "longitude": 126.9780
        },
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        geofence = data.get('geofence', {})
        print(f"✅ 상태: {data.get('status')}")
        print(f"✅ 이벤트: {geofence.get('event')}")
        print(f"✅ 거리: {geofence.get('distance')}m")
        print(f"✅ 집 안: {geofence.get('inside_geofence')}")
        print(f"✅ 접근 중: {geofence.get('approaching')}")
    else:
        print(f"❌ 에러: {response.status_code}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

print("\n" + "=" * 60)
print("테스트 완료!")
print("=" * 60)
