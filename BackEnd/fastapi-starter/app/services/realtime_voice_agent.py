"""
OpenAI Realtime API 기반 음성 에이전트
Speech-to-Speech 양방향 스트림 처리
"""
import os
import json
import logging
import asyncio
import base64
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)


class RealtimeVoiceAgent:
    """
    OpenAI Realtime API 음성 에이전트

    기능:
    - WebSocket 양방향 음성 스트림
    - Speech-to-Speech (STT + LLM + TTS 통합)
    - Function calling으로 가전 제어
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = "gpt-realtime"
        self.api_url = "wss://api.openai.com/v1/realtime?model=" + self.model

        # 세션별 WebSocket 연결
        self.sessions: Dict[str, WebSocketClientProtocol] = {}

        # Function calling 핸들러
        self.function_handlers: Dict[str, Callable] = {}

    def register_function(self, name: str, handler: Callable):
        """
        Function calling 핸들러 등록

        Args:
            name: 함수 이름
            handler: 실행할 핸들러 (async 함수)
        """
        self.function_handlers[name] = handler
        logger.info(f"✅ Registered function: {name}")

    async def create_session(
        self,
        user_id: str,
        instructions: Optional[str] = None,
        voice: str = "shimmer"
    ) -> Dict[str, Any]:
        """
        Realtime API 세션 생성

        Args:
            user_id: 사용자 ID
            instructions: 시스템 프롬프트
            voice: TTS 음성
                - alloy: 중성적, 균형잡힌 (기본)
                - echo: 낮고 침착한 남성
                - fable: 따뜻하고 표현력 있는
                - onyx: 깊고 권위있는 남성
                - nova: 밝고 활기찬 여성 ⭐ 추천
                - shimmer: 부드럽고 명확한 여성 ⭐ 추천

        Returns:
            세션 정보
        """
        try:
            # WebSocket 연결
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }

            # websockets 15.x uses additional_headers instead of extra_headers
            ws = await websockets.connect(
                self.api_url,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )

            self.sessions[user_id] = ws
            logger.info(f"✅ Realtime session created for user {user_id}")

            # 세션 설정
            if instructions is None:
                # 페르소나 없음: 기본 시스템 프롬프트
                instructions = self._build_system_instructions()
            else:
                # 페르소나 있음: 기본 프롬프트 + 페르소나 결합
                base_instructions = self._build_system_instructions()
                instructions = f"{base_instructions}\n\n**페르소나 (말투/성격):**\n{instructions}"

            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": instructions,
                    "voice": voice,
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,  # 음성 감지 민감도 (0.0~1.0)
                        "prefix_padding_ms": 300,  # 음성 시작 전 패딩
                        "silence_duration_ms": 500  # 침묵 감지 시간 (짧을수록 빠른 응답)
                    },
                    "tools": self._get_function_definitions(),
                    "tool_choice": "auto",
                    "temperature": 0.9,  # 0.8 → 0.9 (더 자연스럽고 다양한 응답)
                    "max_response_output_tokens": 2048  # 4096 → 2048 (더 간결한 응답)
                }
            }

            await ws.send(json.dumps(session_config))

            return {
                "status": "connected",
                "user_id": user_id,
                "session_id": id(ws)
            }

        except Exception as e:
            logger.error(f"❌ Session creation error: {str(e)}")
            raise

    def _build_system_instructions(self) -> str:
        """시스템 프롬프트 생성 (텍스트 LLM과 동일한 스타일)"""
        return """당신은 사용자의 스마트홈 AI 어시스턴트입니다.

**역할:**
- 사용자와 자연스럽게 대화
- 집안일 도움 (가전제품 제어, 일정 관리 등)
- 사용자의 상태 파악 (피로도, 스트레스 등)

**가전 제어:**
- 사용자가 "에어컨 켜줘", "불 켜줘" 등을 요청하면 control_appliance 함수를 호출하세요
- "덥다", "춥다", "건조하다" 등 환경 불편 표현이 있으면:
  1. 먼저 get_current_status로 현재 상태를 확인
  2. recommend_appliances로 추천 받기
  3. 사용자에게 제안하고 동의를 구한 후 제어
- 가전 제어 전에는 반드시 사용자에게 확인을 받으세요

**대화 스타일:**
- 자연스럽고 친근하게 대화
- 존댓말 사용
- 간결하지만 따뜻한 응답
- 사용자의 감정과 상태를 고려한 배려
- 불필요한 정보는 생략

**중요:**
- 음성 대화이므로 너무 길게 말하지 마세요 (1-2문장 권장)
- 숫자나 전문용어는 쉽게 풀어서 설명하세요
- 질문은 명확하고 간단하게 하세요
"""

    def _get_function_definitions(self) -> list[Dict[str, Any]]:
        """Function calling 정의"""
        return [
            {
                "type": "function",
                "name": "control_appliance",
                "description": "가전제품을 제어합니다 (켜기/끄기/설정 변경)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "appliance_type": {
                            "type": "string",
                            "enum": ["에어컨", "가습기", "제습기", "공기청정기", "조명", "TV"],
                            "description": "제어할 가전 종류"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["on", "off", "set"],
                            "description": "동작 (on: 켜기, off: 끄기, set: 설정 변경)"
                        },
                        "settings": {
                            "type": "object",
                            "description": "설정값 (예: {\"target_temp_c\": 24, \"fan_speed\": \"mid\"})",
                            "properties": {
                                "target_temp_c": {"type": "number"},
                                "fan_speed": {"type": "string"},
                                "target_humidity_pct": {"type": "number"},
                                "mode": {"type": "string"},
                                "brightness_pct": {"type": "number"}
                            }
                        }
                    },
                    "required": ["appliance_type", "action"]
                }
            },
            {
                "type": "function",
                "name": "get_current_status",
                "description": "현재 날씨와 집안 환경 상태를 조회합니다",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "recommend_appliances",
                "description": "현재 상황에 맞는 가전 제어를 추천받습니다",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    async def send_audio(self, user_id: str, audio_data: bytes):
        """
        음성 데이터 전송

        Args:
            user_id: 사용자 ID
            audio_data: PCM16 오디오 데이터 (16kHz, 16-bit, mono)
        """
        try:
            ws = self.sessions.get(user_id)
            if not ws:
                raise ValueError(f"No session found for user {user_id}")

            # OpenAI Realtime API는 base64 인코딩된 오디오를 JSON으로 전송
            duration_ms = (len(audio_data) / 32000) * 1000  # 16kHz * 2 bytes = 32000 bytes/sec
            logger.info(f"📤 Sending audio chunk: {len(audio_data)} bytes (~{duration_ms:.1f}ms)")

            event = {
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(audio_data).decode('utf-8')
            }
            await ws.send(json.dumps(event))

        except Exception as e:
            logger.error(f"❌ Send audio error: {str(e)}")
            raise

    async def commit_audio(self, user_id: str):
        """
        오디오 버퍼 커밋 (응답 생성 트리거)

        Args:
            user_id: 사용자 ID
        """
        try:
            ws = self.sessions.get(user_id)
            if not ws:
                raise ValueError(f"No session found for user {user_id}")

            # 먼저 오디오 입력 커밋
            commit_event = {
                "type": "input_audio_buffer.commit"
            }
            await ws.send(json.dumps(commit_event))

            # 그 다음 응답 생성 요청
            response_event = {
                "type": "response.create"
            }
            await ws.send(json.dumps(response_event))

        except Exception as e:
            logger.error(f"❌ Commit audio error: {str(e)}")
            raise

    async def handle_events(
        self,
        user_id: str,
        audio_callback: Optional[Callable[[bytes], Awaitable[None]]] = None,
        transcript_callback: Optional[Callable[[str, str], Awaitable[None]]] = None,
        error_callback: Optional[Callable[[str], Awaitable[None]]] = None,
        response_done_callback: Optional[Callable[[], Awaitable[None]]] = None
    ):
        """
        이벤트 스트림 처리

        Args:
            user_id: 사용자 ID
            audio_callback: 오디오 수신 콜백 (audio_data)
            transcript_callback: 텍스트 수신 콜백 (role, text)
            error_callback: 에러 콜백 (error_message)
            response_done_callback: 응답 완료 콜백
        """
        try:
            ws = self.sessions.get(user_id)
            if not ws:
                raise ValueError(f"No session found for user {user_id}")

            logger.info(f"🎧 Started event handling for user {user_id}")

            async for message in ws:
                try:
                    event = json.loads(message)
                    event_type = event.get("type")

                    # 오디오 출력 (AI 음성)
                    if event_type == "response.audio.delta":
                        audio_b64 = event.get("delta")
                        if audio_b64 and audio_callback:
                            audio_data = base64.b64decode(audio_b64)
                            await audio_callback(audio_data)

                    # 텍스트 출력 (AI 응답)
                    elif event_type == "response.text.delta":
                        text = event.get("delta")
                        if text and transcript_callback:
                            await transcript_callback("assistant", text)

                    # 사용자 음성 전사 결과
                    elif event_type == "conversation.item.input_audio_transcription.completed":
                        transcript = event.get("transcript", "")
                        if transcript and transcript_callback:
                            await transcript_callback("user", transcript)
                            logger.info(f"👤 User: {transcript}")

                    # Function calling
                    elif event_type == "response.function_call_arguments.done":
                        await self._handle_function_call(user_id, event)

                    # 응답 완료
                    elif event_type == "response.done":
                        logger.info(f"✅ Response completed")
                        if response_done_callback:
                            await response_done_callback()

                    # 오디오 전사 완료 (응답 음성의 텍스트)
                    elif event_type == "response.audio_transcript.done":
                        transcript = event.get("transcript", "")
                        if transcript and transcript_callback:
                            await transcript_callback("assistant", transcript)
                            logger.info(f"🤖 Assistant: {transcript}")

                    # 에러
                    elif event_type == "error":
                        error_msg = event.get("error", {}).get("message", "Unknown error")
                        logger.error(f"❌ Realtime API error: {error_msg}")
                        if error_callback:
                            await error_callback(error_msg)

                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Failed to parse event: {message}")
                except Exception as e:
                    logger.error(f"❌ Event handling error: {str(e)}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 WebSocket closed for user {user_id}")
            self.sessions.pop(user_id, None)
        except Exception as e:
            logger.error(f"❌ Event loop error: {str(e)}")
            raise

    async def _handle_function_call(self, user_id: str, event: Dict[str, Any]):
        """Function calling 처리"""
        try:
            call_id = event.get("call_id")
            function_name = event.get("name")
            arguments_str = event.get("arguments")

            logger.info(f"🔧 Function call: {function_name}")

            # 인자 파싱
            arguments = json.loads(arguments_str) if arguments_str else {}

            # 핸들러 실행
            handler = self.function_handlers.get(function_name)
            if handler:
                result = await handler(user_id, **arguments)
            else:
                result = {"error": f"Unknown function: {function_name}"}

            # 결과 전송
            ws = self.sessions.get(user_id)
            if ws:
                response_event = {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps(result, ensure_ascii=False)
                    }
                }
                await ws.send(json.dumps(response_event))

                # 응답 생성 요청
                await ws.send(json.dumps({"type": "response.create"}))

        except Exception as e:
            logger.error(f"❌ Function call error: {str(e)}")

    async def close_session(self, user_id: str):
        """
        세션 종료

        Args:
            user_id: 사용자 ID
        """
        try:
            ws = self.sessions.pop(user_id, None)
            if ws:
                await ws.close()
                logger.info(f"✅ Session closed for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Close session error: {str(e)}")


# 싱글톤 인스턴스
realtime_agent = RealtimeVoiceAgent()
