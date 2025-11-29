# app/api/voice_realtime.py
"""
OpenAI Realtime API WebSocket 엔드포인트
Speech-to-Speech 양방향 음성 스트림 처리
"""
import os
import logging
import json
import asyncio
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.services.realtime_voice_agent import realtime_agent
from app.services.appliance_control_service import appliance_control_service
from app.services.appliance_rule_engine import appliance_rule_engine
from app.services.weather_service import weather_service
from app.services.hrv_service import hrv_service
from app.services.supabase_service import supabase_persona_service
import app.cruds.info as infoCruds

logger = logging.getLogger(__name__)
router = APIRouter()


class VoiceRealtimeHandler:
    """
    Realtime Voice Agent WebSocket 핸들러
    클라이언트 ↔ FastAPI ↔ OpenAI Realtime API
    """

    def __init__(self, db: Session, use_manual_commit: bool = False):
        self.db = db
        self.registered_functions = False
        self.use_manual_commit = use_manual_commit  # 테스트용 수동 커밋 모드
        self.audio_buffer = bytearray() if use_manual_commit else None
        self.total_audio_received = 0  # 디버깅용

    def register_function_handlers(self, user_id: str):
        """Function calling 핸들러 등록"""
        if self.registered_functions:
            return

        # 1. 가전 제어
        async def handle_control_appliance(
            uid: str, appliance_type: str, action: str, settings: Dict[str, Any] = None
        ):
            """가전 제어 실행"""
            try:
                logger.info(f"🎛️ Control: {appliance_type} {action} {settings}")
                result = appliance_control_service.execute_command(
                    db=self.db,
                    user_id=uid,
                    appliance_type=appliance_type,
                    action=action,
                    settings=settings,
                    triggered_by="voice_realtime"
                )
                return {
                    "success": True,
                    "appliance": appliance_type,
                    "action": action,
                    "status": result.get("status", "ok"),
                    "message": f"{appliance_type}을(를) {action} 했습니다."
                }
            except Exception as e:
                logger.error(f"❌ Control error: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"제어 중 오류가 발생했습니다: {str(e)}"
                }

        # 2. 현재 상태 조회
        async def handle_get_current_status(uid: str):
            """현재 날씨와 집안 환경 상태 조회"""
            try:
                # 사용자 정보 조회
                user = infoCruds.get_user(self.db, UUID(uid))
                if not user:
                    return {"error": "User not found"}

                # 날씨 정보
                weather_data = await weather_service.get_combined_weather(
                    db=self.db,
                    latitude=user.home_latitude or 37.5665,
                    longitude=user.home_longitude or 126.9780,
                    sido_name="서울"
                )

                # HRV 피로도
                fatigue = hrv_service.get_latest_fatigue_level(self.db, UUID(uid))

                # 가전 상태
                appliances = appliance_control_service.get_appliance_status(
                    db=self.db,
                    user_id=uid
                )

                return {
                    "weather": {
                        "temperature": weather_data.get("temperature"),
                        "humidity": weather_data.get("humidity"),
                        "pm10": weather_data.get("pm10"),
                        "pm2_5": weather_data.get("pm2_5"),
                        "description": weather_data.get("description")
                    },
                    "fatigue_level": fatigue,
                    "appliances": appliances,
                    "message": f"현재 온도 {weather_data.get('temperature')}도, 습도 {weather_data.get('humidity')}%, 피로도 레벨 {fatigue}입니다."
                }
            except Exception as e:
                logger.error(f"❌ Status error: {str(e)}")
                return {"error": str(e)}

        # 3. 가전 제어 추천
        async def handle_recommend_appliances(uid: str):
            """현재 상황 기반 가전 제어 추천"""
            try:
                # 사용자 정보
                user = infoCruds.get_user(self.db, UUID(uid))
                if not user:
                    return {"error": "User not found"}

                # 날씨 정보
                weather_data = await weather_service.get_combined_weather(
                    db=self.db,
                    latitude=user.home_latitude or 37.5665,
                    longitude=user.home_longitude or 126.9780,
                    sido_name="서울"
                )

                # 추천 생성
                recommendations = appliance_rule_engine.get_appliances_to_control(
                    db=self.db,
                    user_id=uid,
                    weather_data=weather_data
                )

                if not recommendations:
                    return {
                        "recommendations": [],
                        "message": "현재는 제어가 필요한 가전이 없습니다."
                    }

                # 추천 메시지 생성
                messages = []
                for rec in recommendations:
                    action_str = "켜기" if rec["action"] == "on" else "끄기" if rec["action"] == "off" else "설정 변경"
                    messages.append(f"{rec['appliance_type']}: {action_str} ({rec['reason']})")

                return {
                    "recommendations": recommendations,
                    "message": "추천: " + ", ".join(messages)
                }
            except Exception as e:
                logger.error(f"❌ Recommend error: {str(e)}")
                return {"error": str(e)}

        # 핸들러 등록
        realtime_agent.register_function("control_appliance", handle_control_appliance)
        realtime_agent.register_function("get_current_status", handle_get_current_status)
        realtime_agent.register_function("recommend_appliances", handle_recommend_appliances)

        self.registered_functions = True
        logger.info("✅ Function handlers registered")

    async def handle_websocket(self, websocket: WebSocket, user_id: str, character_id: str = None):
        """WebSocket 연결 처리"""
        await websocket.accept()
        logger.info(f"🎙️ WebSocket connected: {user_id}, character_id: {character_id}")

        try:
            # Function handlers 등록
            self.register_function_handlers(user_id)

            # 페르소나 로드 (character_id가 있으면)
            persona_instructions = None
            if character_id:
                # 1순위: Supabase 페르소나 시스템 시도
                if supabase_persona_service.is_available():
                    persona_data = supabase_persona_service.get_persona_for_llm(character_id)
                    if persona_data:
                        persona_instructions = persona_data["description"]
                        logger.info(f"✅ Loaded Supabase persona: {persona_data['nickname']}")
                    else:
                        logger.warning(f"⚠️ Supabase persona not found: {character_id}, falling back to FastAPI Character")

                # 2순위: FastAPI Character 테이블 (fallback)
                if not persona_instructions:
                    from app.cruds import info as infoCruds
                    from uuid import UUID
                    character = infoCruds.get_character(self.db, UUID(character_id))
                    if character:
                        persona_instructions = character.persona
                        logger.info(f"✅ Loaded FastAPI persona: {character.nickname}")
                    else:
                        logger.warning(f"⚠️ Character not found in both Supabase and FastAPI DB: {character_id}")

            # Realtime API 세션 생성
            # voice 옵션: alloy(중성), echo(남성/낮음), fable(표현력), onyx(남성/깊음), nova(여성/밝음), shimmer(여성/부드러움)
            session_info = await realtime_agent.create_session(
                user_id=user_id,
                instructions=persona_instructions,  # 페르소나 적용
                voice="shimmer"  # 부드럽고 명확한 여성 음성
            )
            logger.info(f"✅ Realtime session created: {session_info}")

            # 환영 메시지 (선택적)
            await websocket.send_json({
                "type": "session_started",
                "session_id": session_info["session_id"],
                "message": "음성 세션이 시작되었습니다."
            })

            # 오디오 수신 콜백
            async def audio_callback(audio_data: bytes):
                """AI 응답 음성을 클라이언트로 전송"""
                try:
                    await websocket.send_bytes(audio_data)
                except Exception as e:
                    logger.error(f"❌ Audio send error: {str(e)}")

            # 텍스트 수신 콜백 (디버깅용)
            async def transcript_callback(role: str, text: str):
                """음성 전사 결과 전송"""
                try:
                    await websocket.send_json({
                        "type": "transcript",
                        "role": role,
                        "text": text
                    })
                    logger.info(f"📝 {role}: {text}")
                except Exception as e:
                    logger.error(f"❌ Transcript send error: {str(e)}")

            # 에러 콜백
            async def error_callback(error_msg: str):
                """에러 메시지 전송"""
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": error_msg
                    })
                except Exception as e:
                    logger.error(f"❌ Error send error: {str(e)}")

            # 응답 완료 콜백
            async def response_done_callback():
                """응답 완료 알림"""
                try:
                    await websocket.send_json({
                        "type": "response.done"
                    })
                    logger.info("📤 Response done event sent to client")
                except Exception as e:
                    logger.error(f"❌ Response done send error: {str(e)}")

            # 이벤트 처리 태스크 시작
            event_task = asyncio.create_task(
                realtime_agent.handle_events(
                    user_id=user_id,
                    audio_callback=audio_callback,
                    transcript_callback=transcript_callback,
                    error_callback=error_callback,
                    response_done_callback=response_done_callback
                )
            )

            # 클라이언트로부터 메시지 수신
            while True:
                try:
                    # FastAPI WebSocket의 receive() 메서드 사용
                    data = await websocket.receive()

                    # WebSocket disconnect 이벤트 처리
                    if data.get("type") == "websocket.disconnect":
                        logger.info(f"🔌 WebSocket disconnected: {user_id}")
                        break

                    # 바이너리 오디오 데이터 처리
                    if "bytes" in data:
                        bytes_data = data["bytes"]
                        self.total_audio_received += len(bytes_data)

                        if self.use_manual_commit:
                            # 테스트 모드: 버퍼에 쌓기
                            self.audio_buffer.extend(bytes_data)
                            duration_ms = (len(self.audio_buffer) / 32000) * 1000
                            logger.info(f"🎤 Audio chunk received: {len(bytes_data)} bytes (buffer: {len(self.audio_buffer)} bytes, ~{duration_ms:.1f}ms)")
                        else:
                            # 실시간 모드: 즉시 전송 (Server VAD가 자동으로 처리)
                            logger.info(f"🎤 Audio chunk received: {len(bytes_data)} bytes (realtime streaming)")
                            await realtime_agent.send_audio(user_id, bytes_data)

                    # 텍스트 메시지 처리 (JSON 제어 명령)
                    elif "text" in data:
                        text_data = data["text"]
                        try:
                            msg = json.loads(text_data)
                            msg_type = msg.get("type")

                            if msg_type == "audio_commit":
                                if self.use_manual_commit:
                                    # 테스트 모드: 버퍼에 있는 모든 오디오를 한 번에 전송
                                    if self.audio_buffer and len(self.audio_buffer) > 0:
                                        duration_ms = (len(self.audio_buffer) / 32000) * 1000
                                        logger.info(f"📤 Sending buffered audio: {len(self.audio_buffer)} bytes (~{duration_ms:.1f}ms)")
                                        await realtime_agent.send_audio(user_id, bytes(self.audio_buffer))
                                        self.audio_buffer.clear()

                                        await asyncio.sleep(0.1)
                                        logger.info("📤 Committing audio buffer")
                                        await realtime_agent.commit_audio(user_id)
                                    else:
                                        logger.warning("⚠️ No audio in buffer to commit")
                                else:
                                    # 실시간 모드: Server VAD가 자동 처리하므로 수동 커밋 불필요
                                    logger.info("📤 Manual commit ignored (Server VAD enabled)")

                            elif msg_type == "close":
                                logger.info(f"🔌 Client requested close: {user_id}")
                                break
                            else:
                                logger.warning(f"⚠️ Unknown message type: {msg_type}")
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Invalid JSON: {text_data[:100]}")

                except WebSocketDisconnect:
                    logger.info(f"🔌 WebSocket disconnected (exception): {user_id}")
                    break
                except Exception as e:
                    logger.error(f"❌ Receive error: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    break

            # 정리
            try:
                event_task.cancel()
                await event_task  # 태스크가 완전히 종료될 때까지 대기
            except asyncio.CancelledError:
                logger.info(f"✅ Event task cancelled for user {user_id}")
            except Exception as e:
                logger.error(f"❌ Event task cleanup error: {str(e)}")
            finally:
                await realtime_agent.close_session(user_id)

        except Exception as e:
            logger.error(f"❌ WebSocket handler error: {str(e)}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": f"서버 오류: {str(e)}"
                })
            except:
                pass
        finally:
            try:
                await websocket.close()
            except:
                pass
            logger.info(f"✅ WebSocket closed: {user_id}")


@router.websocket("/ws/voice/{user_id}")
async def websocket_voice_endpoint(
    websocket: WebSocket,
    user_id: str,
    character_id: str = None,  # Query parameter로 페르소나 선택
    db: Session = Depends(get_db)
):
    """
    OpenAI Realtime API 음성 WebSocket 엔드포인트

    프로토콜:
    - Client → Server: 바이너리 오디오 데이터 (PCM16, 16kHz, mono)
    - Client → Server: JSON 제어 메시지 {"type": "audio_commit"} 또는 {"type": "close"}
    - Server → Client: 바이너리 오디오 데이터 (AI 응답)
    - Server → Client: JSON 이벤트 메시지 (transcript, error, session_started)

    사용 예시:
    ```javascript
    const ws = new WebSocket('ws://localhost:11325/api/voice/ws/voice/user_123');

    // 오디오 전송
    ws.send(audioBuffer);  // PCM16 ArrayBuffer

    // 응답 생성 요청
    ws.send(JSON.stringify({type: 'audio_commit'}));

    // 오디오 수신
    ws.onmessage = (event) => {
        if (event.data instanceof Blob) {
            // AI 음성 재생
            playAudio(event.data);
        } else {
            // JSON 이벤트 처리
            const data = JSON.parse(event.data);
            console.log(data.type, data);
        }
    };
    ```
    """
    # 환경 변수로 수동 커밋 모드 설정
    # VOICE_MANUAL_COMMIT=true: 수동 커밋 (테스트용)
    # VOICE_MANUAL_COMMIT=false: Server VAD 자동 처리 (실제 서비스)
    use_manual_commit = os.getenv("VOICE_MANUAL_COMMIT", "true").lower() == "true"
    handler = VoiceRealtimeHandler(db, use_manual_commit=use_manual_commit)
    await handler.handle_websocket(websocket, user_id, character_id)
