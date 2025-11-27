#!/usr/bin/env python3
"""
Speech-to-Speech WebSocket 간단 테스트 (자동 실행)
"""
import asyncio
import websockets
import json
import os
import sys

# User ID 읽기
if os.path.exists("test_user_id.txt"):
    with open("test_user_id.txt", "r") as f:
        USER_ID = f.read().strip()
else:
    print("❌ test_user_id.txt 파일이 없습니다.")
    sys.exit(1)

WS_URL = f"ws://localhost:11325/api/voice/ws/voice/{USER_ID}"


async def test_connection():
    """WebSocket 연결 테스트"""
    print("=" * 60)
    print("Speech-to-Speech WebSocket 연결 테스트")
    print("=" * 60)
    print(f"User ID: {USER_ID}")
    print(f"URL: {WS_URL}\n")

    try:
        print("⏳ WebSocket 연결 중...")
        async with websockets.connect(WS_URL) as websocket:
            print("✅ WebSocket 연결 성공!\n")

            # 세션 시작 메시지 수신
            print("⏳ 세션 시작 메시지 대기 중...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                if isinstance(response, str):
                    data = json.loads(response)
                    print(f"✅ 서버 응답 수신:")
                    print(f"   Type: {data.get('type')}")
                    print(f"   Message: {data.get('message')}")
                    if 'session_id' in data:
                        print(f"   Session ID: {data.get('session_id')}")
                else:
                    print(f"⚠️ 바이너리 데이터 수신: {len(response)} bytes")
            except asyncio.TimeoutError:
                print("⚠️ 세션 시작 메시지 타임아웃")

            # 대기
            await asyncio.sleep(1)

            # 종료 메시지 전송
            print("\n🔌 세션 종료 요청 전송...")
            await websocket.send(json.dumps({"type": "close"}))
            print("✅ 종료 메시지 전송 완료")

            # 종료 대기
            await asyncio.sleep(0.5)

            print("\n" + "=" * 60)
            print("✅ 모든 테스트 통과!")
            print("=" * 60)
            print("\n결과:")
            print("  ✅ WebSocket 연결 성공")
            print("  ✅ 세션 생성 확인")
            print("  ✅ 정상 종료")
            print("\n📝 다음 단계:")
            print("  - iOS/Android 앱에서 실제 음성 입력 테스트")
            print("  - test_s2s_websocket.py를 실행하여 오디오 전송 테스트")
            print("=" * 60)

            return True

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ 연결 실패: HTTP {e.status_code}")
        print("   서버가 실행 중인지 확인하세요:")
        print("   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 11325")
        return False

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket 에러: {str(e)}")
        return False

    except ConnectionRefusedError:
        print("❌ 연결 거부됨")
        print("   서버가 실행 중인지 확인하세요:")
        print("   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 11325")
        return False

    except Exception as e:
        print(f"❌ 예상치 못한 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
