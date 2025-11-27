#!/usr/bin/env python3
"""
간단한 API 수동 테스트
"""
import requests
import json

BASE_URL = "http://localhost:11325/api"

print("=" * 60)
print("SPACE API 수동 테스트")
print("=" * 60)

# 1. 통합 날씨 API 테스트 (날씨 + 대기질)
print("\n1️⃣ 통합 날씨 + 대기질 API 테스트")
print("-" * 60)
try:
    response = requests.get(
        f"{BASE_URL}/weather/current",
        params={"latitude": 37.5665, "longitude": 126.9780, "sido": "서울"},
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 온도: {data.get('temperature')}°C")
        print(f"✅ 습도: {data.get('humidity')}%")
        print(f"✅ PM10: {data.get('pm10')} ㎍/㎥")
        print(f"✅ PM2.5: {data.get('pm2_5')} ㎍/㎥")
        print(f"✅ 캐시: {data.get('cached')}")
    else:
        print(f"❌ 에러: {response.status_code} - {response.text[:100]}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 2. 가전 추천 API 테스트
print("\n2️⃣ 가전 추천 API 테스트")
print("-" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/appliances/recommend/test_user",
        json={
            "latitude": 37.5665,
            "longitude": 126.9780,
            "sido": "서울"
        },
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        recs = data.get("recommendations", [])
        print(f"✅ 추천: {len(recs)}개 가전")
        for rec in recs[:3]:
            print(f"   - {rec.get('appliance_type')}: {rec.get('action')}")
    else:
        print(f"❌ 에러: {response.status_code} - {response.text[:100]}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 5. Chat API 테스트
print("\n5️⃣ Chat API 테스트 (일반 대화)")
print("-" * 60)
try:
    response = requests.post(
        f"{BASE_URL}/chat/test_user/message",
        json={"message": "안녕하세요!", "context": {}},
        timeout=30
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ AI 응답: {data.get('ai_response')}")
        print(f"✅ 의도: {data.get('intent_type')}")
    else:
        print(f"❌ 에러: {response.status_code} - {response.text[:100]}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

# 6. 히스토리 조회
print("\n6️⃣ Chat 히스토리 조회")
print("-" * 60)
try:
    response = requests.get(
        f"{BASE_URL}/chat/test_user/history",
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        history = data.get("conversation_history", [])
        print(f"✅ 대화 내역: {len(history)}개")
    else:
        print(f"❌ 에러: {response.status_code} - {response.text[:100]}")
except Exception as e:
    print(f"❌ 실패: {str(e)}")

print("\n" + "=" * 60)
print("테스트 완료!")
print("=" * 60)
