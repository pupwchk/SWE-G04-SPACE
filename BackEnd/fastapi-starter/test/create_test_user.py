#!/usr/bin/env python3
"""
테스트 사용자 생성 스크립트
"""
import requests
import json

BASE_URL = "http://localhost:11325/api"

print("=" * 60)
print("테스트 사용자 생성")
print("=" * 60)

# 사용자 생성
print("\n사용자 생성 중...")
try:
    response = requests.post(
        f"{BASE_URL}/users/",
        json={
            "username": "test_user",
            "email": "test@example.com",
            "home_latitude": 37.5665,
            "home_longitude": 126.9780
        },
        timeout=10
    )

    if response.status_code in [200, 201]:
        user = response.json()
        user_id = user.get("id")
        print(f"✅ 사용자 생성 성공!")
        print(f"   User ID: {user_id}")
        print(f"   Username: {user.get('username')}")
        print(f"   Email: {user.get('email')}")

        # UUID를 파일에 저장
        with open("test_user_id.txt", "w") as f:
            f.write(str(user_id))

        print(f"\n✅ User ID가 test_user_id.txt 파일에 저장되었습니다.")
        print(f"\n다음 명령어로 테스트하세요:")
        print(f"  USER_ID=$(cat test_user_id.txt)")
        print(f"  echo $USER_ID")

    else:
        print(f"❌ 에러: {response.status_code}")
        print(f"   {response.text}")

except Exception as e:
    print(f"❌ 실패: {str(e)}")

print("\n" + "=" * 60)
