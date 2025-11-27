#!/usr/bin/env python3
"""
Speech-to-Speech WebSocket 테스트 클라이언트
"""
import asyncio
import websockets
import json
import os
import sys
import struct
import wave
from pathlib import Path

# User ID 읽기
if os.path.exists("test_user_id.txt"):
    with open("test_user_id.txt", "r") as f:
        USER_ID = f.read().strip()
else:
    print("❌ test_user_id.txt 파일이 없습니다. create_test_user.py를 먼저 실행하세요.")
    sys.exit(1)

WS_URL = f"ws://localhost:11325/api/voice/ws/voice/{USER_ID}"


def create_test_audio():
    """
    테스트용 오디오 생성 (PCM16, 16kHz, mono)
    실제로는 마이크 입력을 사용해야 함
    """
    # 1초간 440Hz 사인파 (A4 음)
    import math
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0

    samples = []
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        value = math.sin(2 * math.pi * frequency * t)
        # -32768 ~ 32767 범위로 변환
        sample = int(value * 32767)
        # 16-bit little-endian PCM
        samples.append(struct.pack('<h', sample))

    return b''.join(samples)


async def test_websocket_simple():
    """
    간단한 WebSocket 연결 테스트 (텍스트 메시지만)
    """
    print("=" * 60)
    print("Speech-to-Speech WebSocket 연결 테스트")
    print("=" * 60)
    print(f"User ID: {USER_ID}")
    print(f"Connecting to: {WS_URL}\n")

    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ WebSocket 연결 성공!")

            # 세션 시작 메시지 수신
            response = await websocket.recv()
            if isinstance(response, str):
                data = json.loads(response)
                print(f"📨 서버 메시지: {data.get('type')} - {data.get('message')}")

            print("\n테스트 시나리오:")
            print("1. 텍스트 메시지 전송 테스트")
            print("2. 세션 종료 요청")

            # 대기
            await asyncio.sleep(1)

            # 종료 메시지 전송
            print("\n🔌 세션 종료 요청 중...")
            await websocket.send(json.dumps({"type": "close"}))

            # 종료 대기
            await asyncio.sleep(0.5)

            print("✅ WebSocket 테스트 완료!")

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket 에러: {str(e)}")
    except Exception as e:
        print(f"❌ 실패: {str(e)}")


async def test_websocket_with_audio():
    """
    오디오 전송 포함 WebSocket 테스트
    """
    print("=" * 60)
    print("Speech-to-Speech 오디오 전송 테스트")
    print("=" * 60)
    print(f"User ID: {USER_ID}")
    print(f"Connecting to: {WS_URL}\n")

    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ WebSocket 연결 성공!")

            # 세션 시작 메시지 수신
            response = await websocket.recv()
            if isinstance(response, str):
                data = json.loads(response)
                print(f"📨 {data.get('type')}: {data.get('message')}")
                print(f"   Session ID: {data.get('session_id')}")

            print("\n🎙️ 테스트 오디오 생성 중...")
            test_audio = create_test_audio()
            print(f"✅ 오디오 생성 완료 ({len(test_audio)} bytes)")

            print("\n📤 오디오 데이터 전송 중...")
            # 오디오를 작은 청크로 나눠서 전송 (실제 마이크 입력 시뮬레이션)
            chunk_size = 4096
            for i in range(0, len(test_audio), chunk_size):
                chunk = test_audio[i:i + chunk_size]
                await websocket.send(chunk)
                await asyncio.sleep(0.05)  # 50ms 간격

            print("✅ 오디오 전송 완료")

            print("\n📤 응답 생성 요청...")
            await websocket.send(json.dumps({"type": "audio_commit"}))

            print("\n⏳ AI 응답 대기 중 (최대 10초)...")
            received_audio = False
            received_transcript = False

            try:
                # 응답 수신 (타임아웃 10초)
                for _ in range(20):  # 10초 / 0.5초
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.5)

                        if isinstance(response, bytes):
                            print(f"🔊 오디오 응답 수신: {len(response)} bytes")
                            received_audio = True
                        elif isinstance(response, str):
                            data = json.loads(response)
                            msg_type = data.get('type')

                            if msg_type == 'transcript':
                                print(f"📝 {data.get('role')}: {data.get('text')}")
                                received_transcript = True
                            elif msg_type == 'error':
                                print(f"❌ 에러: {data.get('message')}")
                            else:
                                print(f"📨 {msg_type}: {data}")

                    except asyncio.TimeoutError:
                        continue

            except Exception as e:
                print(f"⚠️ 응답 수신 중 에러: {str(e)}")

            # 결과 요약
            print("\n" + "=" * 60)
            print("테스트 결과:")
            print(f"  - 오디오 응답: {'✅ 수신' if received_audio else '❌ 미수신'}")
            print(f"  - 텍스트 전사: {'✅ 수신' if received_transcript else '❌ 미수신'}")
            print("=" * 60)

            # 종료
            print("\n🔌 세션 종료 중...")
            await websocket.send(json.dumps({"type": "close"}))
            await asyncio.sleep(0.5)

            print("✅ 테스트 완료!")

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket 에러: {str(e)}")
    except Exception as e:
        print(f"❌ 실패: {str(e)}")
        import traceback
        traceback.print_exc()


def print_menu():
    """메뉴 출력"""
    print("\n" + "=" * 60)
    print("Speech-to-Speech WebSocket 테스트 메뉴")
    print("=" * 60)
    print("1. 간단한 연결 테스트 (텍스트만)")
    print("2. 오디오 전송 테스트 (생성된 오디오)")
    print("3. 종료")
    print("=" * 60)


async def main():
    """메인 함수"""
    while True:
        print_menu()
        choice = input("\n선택하세요 (1-3): ").strip()

        if choice == "1":
            await test_websocket_simple()
        elif choice == "2":
            await test_websocket_with_audio()
        elif choice == "3":
            print("\n👋 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다. 1-3 중에서 선택하세요.")

        input("\n계속하려면 Enter를 누르세요...")


if __name__ == "__main__":
    print("""
⚠️ 참고사항:
- 이 스크립트는 WebSocket 연결과 기본 프로토콜을 테스트합니다
- 실제 음성 입력은 마이크를 사용하는 클라이언트 앱이 필요합니다
- OpenAI Realtime API는 PCM16, 16kHz, mono 형식을 요구합니다
- 실제 서비스에서는 iOS/Android 앱에서 음성을 녹음하여 전송해야 합니다
""")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 사용자가 종료했습니다.")
    except Exception as e:
        print(f"\n❌ 에러: {str(e)}")
        import traceback
        traceback.print_exc()
