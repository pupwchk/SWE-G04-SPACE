# app/api/voice_realtime.py
"""
OpenAI Realtime API WebSocket 엔드포인트
Speech-to-Speech 양방향 음성 스트림 처리
"""
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
import app.cruds.info as infoCruds

logger = logging.getLogger(__name__)
router = APIRouter()


class VoiceRealtimeHandler:
    """
    Realtime Voice Agent WebSocket 핸들러
    클라이언트 ↔ FastAPI ↔ OpenAI Realtime API
    """

    def __init__(self, db: Session):
        self.db = db
        self.registered_functions = False

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

    async def handle_websocket(self, websocket: WebSocket, user_id: str):
        """WebSocket 연결 처리"""
        await websocket.accept()
        logger.info(f"🎙️ WebSocket connected: {user_id}")

        try:
            # Function handlers 등록
            self.register_function_handlers(user_id)

            # Realtime API 세션 생성
            session_info = await realtime_agent.create_session(
                user_id=user_id,
                voice="alloy"
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

            # 이벤트 처리 태스크 시작
            event_task = asyncio.create_task(
                realtime_agent.handle_events(
                    user_id=user_id,
                    audio_callback=audio_callback,
                    transcript_callback=transcript_callback,
                    error_callback=error_callback
                )
            )

            # 클라이언트로부터 메시지 수신
            while True:
                try:
                    message = await websocket.receive()
                    logger.info(f"👉 RAW MSG RECV: Type={type(message)}, Msg={str(message)[:250]}")

                    text_data = None
                    bytes_data = None

                    if isinstance(message, dict):
                        logger.info("👉 MSG PATH: DICT")
                        if message.get("type") == "websocket.disconnect":
                            logger.info(f"🔌 WebSocket disconnected (event): {user_id}")
                            break
                        text_data = message.get("text")
                        bytes_data = message.get("bytes")
                    elif isinstance(message, str):
                        logger.info("👉 MSG PATH: STR")
                        text_data = message
                    elif isinstance(message, bytes):
                        logger.info("👉 MSG PATH: BYTES")
                        bytes_data = message
                    else:
                        logger.warning(f"👉 MSG PATH: UNKNOWN! Type={type(message)}")


                    if bytes_data:
                        logger.info(f"👉 AUDIO SEND: Passing {len(bytes_data)} bytes to realtime_agent")
                        await realtime_agent.send_audio(user_id, bytes_data)
                    elif text_data:
                        logger.info(f"👉 TEXT PROC: Processing text data: {text_data}")
                        data = json.loads(text_data)
                        msg_type = data.get("type")

                        if msg_type == "audio_commit":
                            logger.info("👉 COMMITTING AUDIO")
                            await realtime_agent.commit_audio(user_id)
                        elif msg_type == "close":
                            logger.info(f"🔌 Client requested close: {user_id}")
                            break
                    else:
                        logger.warning("👉 NO DATA TO PROCESS in received message.")


                except WebSocketDisconnect:
                    logger.info(f"🔌 WebSocket disconnected (exception): {user_id}")
                    break
                except json.JSONDecodeError:
                    logger.warning("⚠️ Invalid JSON received")
                except Exception as e:
                    logger.error(f"❌ Receive error: {str(e)}")
                    break

            # 정리
            event_task.cancel()
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
    handler = VoiceRealtimeHandler(db)
    await handler.handle_websocket(websocket, user_id)
