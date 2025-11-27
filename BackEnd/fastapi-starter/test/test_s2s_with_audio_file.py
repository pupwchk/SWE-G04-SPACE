#!/usr/bin/env python3
"""
Speech-to-Speech 음성 파일 기반 테스트
2회 왕복 대화 테스트
"""
import asyncio
import websockets
import json
import os
import sys
import wave
import struct
from pathlib import Path

# User ID 읽기
if os.path.exists("test_user_id.txt"):
    with open("test_user_id.txt", "r") as f:
        USER_ID = f.read().strip()
else:
    print("❌ test_user_id.txt 파일이 없습니다.")
    sys.exit(1)

WS_URL = f"ws://localhost:11325/api/voice/ws/voice/{USER_ID}"


def load_audio_file(file_path: str) -> bytes:
    """
    음성 파일 로드 (WAV, PCM16, 16kHz, mono)
    헤더(44 bytes)를 제외한 순수 PCM 데이터만 반환합니다.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    if not file_path.endswith('.wav'):
        raise ValueError(f"WAV 파일만 지원합니다: {file_path}")

    # wave 모듈로 포맷 검증
    with wave.open(file_path, 'rb') as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        print(f"   파일 정보 (wave 모듈): {channels}ch, {sample_width*8}bit, {framerate}Hz")
        if channels != 1 or sample_width != 2 or framerate != 16000:
            raise ValueError("오디오는 16kHz, 16-bit, mono PCM 형식이어야 합니다.")

    # 사용자님의 분석에 따라, 헤더를 건너뛰고 데이터만 읽습니다.
    with open(file_path, 'rb') as f:
        f.seek(44)  # 44바이트 헤더 건너뛰기
        pcm_data = f.read()
        return pcm_data


async def test_conversation_with_audio(audio_files: list):
    """
    음성 파일로 2회 왕복 대화 테스트

    Args:
        audio_files: 음성 파일 경로 리스트 (최소 2개)
    """
    print("=" * 70)
    print("Speech-to-Speech 음성 파일 기반 대화 테스트")
    print("=" * 70)
    print(f"User ID: {USER_ID}")
    print(f"WebSocket URL: {WS_URL}")
    print(f"테스트할 음성 파일 개수: {len(audio_files)}개\n")

    try:
        async with websockets.connect(WS_URL, ping_interval=30) as websocket:
            print("✅ WebSocket 연결 성공!\n")

            # 세션 시작 메시지 수신
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            if isinstance(response, str):
                data = json.loads(response)
                print(f"📨 {data.get('type')}: {data.get('message')}")
                print(f"   Session ID: {data.get('session_id')}\n")

            # 수신한 오디오 저장용
            received_audios = []

            # 각 음성 파일로 대화
            for turn, audio_file in enumerate(audio_files, 1):
                print("=" * 70)
                print(f"🎤 Turn {turn}: {audio_file}")
                print("=" * 70)

                # 음성 파일 로드
                try:
                    print(f"📂 음성 파일 로드 중: {audio_file}")
                    audio_data = load_audio_file(audio_file)
                    print(f"✅ 로드 완료 ({len(audio_data)} bytes, {len(audio_data)/32000:.1f}초)")
                except Exception as e:
                    print(f"❌ 파일 로드 실패: {str(e)}")
                    continue

                # 오디오 전송 (청크 단위)
                print(f"\n📤 오디오 전송 중...")
                chunk_size = 4096
                chunks_sent = 0

                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    await websocket.send(chunk)
                    chunks_sent += 1
                    # 실제 녹음 속도 시뮬레이션 (16kHz, 16bit = 32000 bytes/sec)
                    await asyncio.sleep(len(chunk) / 32000)

                print(f"✅ 전송 완료 ({chunks_sent}개 청크)")

                # 응답 생성 요청
                print(f"\n📤 응답 생성 요청 (audio_commit)...")
                await websocket.send(json.dumps({"type": "audio_commit"}))

                # AI 응답 수신
                print(f"\n⏳ AI 응답 대기 중...\n")
                turn_audio = []
                transcript_received = False
                assistant_responded = False
                start_time = asyncio.get_event_loop().time()
                timeout = 20.0

                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        print(f"⚠️ 타임아웃 ({timeout}초)")
                        break

                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=min(2.0, timeout - elapsed)
                        )

                        if isinstance(response, bytes):
                            turn_audio.append(response)
                            print(f"🔊 오디오 수신: {len(response)} bytes (총 {sum(len(a) for a in turn_audio)} bytes)")
                            assistant_responded = True

                        elif isinstance(response, str):
                            data = json.loads(response)
                            msg_type = data.get('type')
                            print(f"📨 이벤트: {msg_type}")

                            if msg_type == 'transcript' and data.get('role') == 'user':
                                print(f"📝 [USER]: {data.get('text')}")
                            
                            elif msg_type == 'transcript' and data.get('role') == 'assistant':
                                print(f"📝 [ASSISTANT]: {data.get('text')}")
                                transcript_received = True
                                assistant_responded = True
                            
                            elif msg_type == 'response.done':
                                print(f"✅ 응답 완료")
                                if assistant_responded:
                                    await asyncio.sleep(1.0)
                                    break
                            
                            elif msg_type == 'error':
                                print(f"❌ 에러: {data.get('message')}")
                                break

                    except asyncio.TimeoutError:
                        if assistant_responded:
                            print(f"✅ 응답 수신 완료 (타임아웃으로 대기 종료)")
                            break
                        else:
                            continue
                    except Exception as e:
                        print(f"⚠️ 수신 중 에러: {str(e)}")
                        break

                # 수신한 오디오 저장
                if turn_audio:
                    total_audio = b''.join(turn_audio)
                    received_audios.append({
                        'turn': turn,
                        'audio': total_audio,
                        'input_file': audio_file
                    })

                    output_file = f"response_turn{turn}.wav"
                    save_as_wav(total_audio, output_file)
                    print(f"\n💾 응답 오디오 저장: {output_file} ({len(total_audio)} bytes, {len(total_audio)/32000:.1f}초)")

                print(f"\n{'='*70}\n")

                if turn < len(audio_files):
                    await asyncio.sleep(1.0)

            # 세션 종료
            print("🔌 세션 종료 요청...")
            await websocket.send(json.dumps({"type": "close"}))
            await asyncio.sleep(0.5)

            # 결과 요약
            print("\n" + "=" * 70)
            print("📊 테스트 결과 요약")
            print("=" * 70)
            print(f"총 대화 턴: {len(audio_files)}회")
            print(f"AI 응답 수신: {len(received_audios)}회")

            for item in received_audios:
                duration = len(item['audio']) / 32000
                print(f"  Turn {item['turn']}: {duration:.1f}초 ({item['input_file']})")
            
            print("=" * 70)

            if len(received_audios) < len(audio_files):
                print("\n❌ 테스트 실패: 일부 응답을 수신하지 못했습니다.")
                return False
            else:
                print("\n✅ 모든 테스트 턴 성공!")
                return True

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket 에러: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def save_as_wav(pcm_data: bytes, output_file: str):
    """PCM 데이터를 WAV 파일로 저장"""
    with wave.open(output_file, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(pcm_data)


async def main():
    """메인 함수"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║  Speech-to-Speech 음성 파일 기반 테스트                          ║
║                                                                   ║
║  이 스크립트는 음성 파일을 입력으로 사용하여                    ║
║  OpenAI Realtime API와 2회 왕복 대화를 테스트합니다.            ║
╚═══════════════════════════════════════════════════════════════════╝
""")

    script_dir = Path(__file__).parent
    audio_files = [str(script_dir / "input1.pcm"), str(script_dir / "input2.pcm")]
    print("=" * 70)
    print("🎤 음성 파일 설정")
    print("=" * 70)
    
    all_files_exist = True
    for file_path in audio_files:
        if not os.path.exists(file_path):
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
            all_files_exist = False
    
    if not all_files_exist:
        return 1
        
    print(f"  - Turn 1: {os.path.basename(audio_files[0])}")
    print(f"  - Turn 2: {os.path.basename(audio_files[1])}")
    print("\n✅ 지정된 파일로 2회 대화를 테스트합니다.")
    print("=" * 70)

    print("\n⏳ 테스트 시작...")
    print()

    result = await test_conversation_with_audio(audio_files)

    if result:
        print("\n✅ 모든 테스트가 성공적으로 완료되었습니다!")
        print("\n📁 생성된 파일:")
        for i in range(1, len(audio_files) + 1):
            output_file = f"response_turn{i}.wav"
            if os.path.exists(output_file):
                print(f"   - {output_file}")
    else:
        print("\n❌ 테스트 실패")
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 사용자가 중단했습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 에러: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)