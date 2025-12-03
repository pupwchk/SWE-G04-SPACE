#!/usr/bin/env python3
"""
시연용 스크립트 - AI 자동 전화 트리거

사용법:
    python3 trigger_demo.py
"""

import urllib.request
import json

# 사용자 이메일 (필요시 수정)
USER_EMAIL = "djwnsgh0248@gmail.com"

# API 엔드포인트
# Docker 환경: localhost:80 (Nginx를 통해)
# 또는 직접: localhost:11325
url = f"http://13.125.85.158:11325/api/location/trigger/demo/{USER_EMAIL}"

print(f"🎬 시연용 AI 자동 전화 트리거 중...")
print(f"   사용자: {USER_EMAIL}")
print(f"   URL: {url}")
print()

try:
    # POST 요청
    req = urllib.request.Request(url, method='POST')
    req.add_header('Content-Type', 'application/json')

    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())

        print("✅ 성공!")
        print(f"   상태: {data.get('status')}")
        print(f"   메시지: {data.get('message')}")
        print()
        print("📱 iOS 앱에서 잠시 후 전화가 올 것입니다...")

except urllib.error.HTTPError as e:
    print(f"❌ 에러 발생: {e.code}")
    print(f"   {e.read().decode()}")

except Exception as e:
    print(f"❌ 에러: {str(e)}")
