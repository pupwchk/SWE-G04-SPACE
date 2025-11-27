#!/usr/bin/env python3
"""
Sendbird 통합 테스트 스크립트
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_001"

def print_section(title):
    """섹션 제목 출력"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_location_update():
    """위치 업데이트 테스트"""
    print_section("1. 위치 업데이트 테스트")
    
    # 집 밖 위치 (서울역)
    outside_location = {
        "user_id": TEST_USER_ID,
        "latitude": 37.5547,
        "longitude": 126.9707,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"\n📍 집 밖 위치로 업데이트: {outside_location['latitude']}, {outside_location['longitude']}")
    response = requests.post(f"{BASE_URL}/api/location/update", json=outside_location)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    time.sleep(2)
    
    # 집 안 위치 (광화문)
    inside_location = {
        "user_id": TEST_USER_ID,
        "latitude": 37.5665,
        "longitude": 126.9780,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"\n📍 집 안 위치로 업데이트: {inside_location['latitude']}, {inside_location['longitude']}")
    response = requests.post(f"{BASE_URL}/api/location/update", json=inside_location)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_location_status():
    """위치 상태 조회 테스트"""
    print_section("2. 위치 상태 조회 테스트")
    
    response = requests.get(f"{BASE_URL}/api/location/status/{TEST_USER_ID}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_geofence_config():
    """Geofence 설정 조회 테스트"""
    print_section("3. Geofence 설정 조회 테스트")
    
    response = requests.get(f"{BASE_URL}/api/location/geofence/config")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_voice_tts():
    """TTS 테스트"""
    print_section("4. TTS 테스트")
    
    tts_request = {
        "text": "안녕하세요! 집에 오신 것을 환영합니다.",
        "user_id": TEST_USER_ID
    }
    
    print(f"\n🔊 TTS 요청: {tts_request['text']}")
    response = requests.post(f"{BASE_URL}/api/voice/tts", json=tts_request)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        # 오디오 파일 저장
        with open("test_tts_output.mp3", "wb") as f:
            f.write(response.content)
        print("✅ TTS 오디오 파일 저장됨: test_tts_output.mp3")
    else:
        print(f"❌ Error: {response.text}")

def test_voice_conversation():
    """음성 대화 테스트"""
    print_section("5. 음성 대화 테스트")
    
    conversation_request = {
        "user_id": TEST_USER_ID,
        "text": "지금 집 온도가 어때?",
        "context": {
            "location": "home",
            "time": datetime.now().isoformat()
        }
    }
    
    print(f"\n💬 대화 요청: {conversation_request['text']}")
    response = requests.post(f"{BASE_URL}/api/voice/conversation", json=conversation_request)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_webhook_chat():
    """채팅 웹훅 시뮬레이션 테스트"""
    print_section("6. 채팅 웹훅 시뮬레이션 테스트")
    
    webhook_payload = {
        "category": "group_channel:message_send",
        "app_id": "0F6FDC87-CA8C-4810-B39F-AD2C235FC05D",
        "channel": {
            "channel_url": "test_channel_001",
            "name": "Test Channel"
        },
        "sender": {
            "user_id": TEST_USER_ID,
            "nickname": "Test User"
        },
        "payload": {
            "message": "안녕하세요, 집 온도를 높여주세요."
        },
        "created_at": int(time.time() * 1000)
    }
    
    print(f"\n📨 웹훅 메시지: {webhook_payload['payload']['message']}")
    response = requests.post(f"{BASE_URL}/api/webhook/sendbird/chat", json=webhook_payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def main():
    """메인 테스트 실행"""
    print("\n" + "🚀 Sendbird 통합 테스트 시작".center(60, "="))
    print(f"Base URL: {BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    
    try:
        # 1. 위치 업데이트 테스트
        test_location_update()
        
        # 2. 위치 상태 조회
        test_location_status()
        
        # 3. Geofence 설정 조회
        test_geofence_config()
        
        # 4. TTS 테스트
        test_voice_tts()
        
        # 5. 음성 대화 테스트
        test_voice_conversation()
        
        # 6. 채팅 웹훅 테스트
        test_webhook_chat()
        
        print("\n" + "✅ 모든 테스트 완료".center(60, "=") + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        print("   실행 명령: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    main()

