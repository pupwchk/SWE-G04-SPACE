"""
Sendbird Webhook API
채팅 메시지 수신 및 처리
"""
import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional

from app.services.sendbird_client import SendbirdChatClient, SendbirdCallsClient
from app.services.llm_service import llm_service, memory_service, LLMAction
from app.services.supabase_service import supabase_persona_service
from app.config.sendbird import SendbirdConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook/sendbird", tags=["Sendbird Webhook"])

# 클라이언트 초기화
chat_client = SendbirdChatClient()
calls_client = SendbirdCallsClient()


@router.post("/chat")
async def sendbird_chat_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Sendbird 채팅 웹훅 수신

    Webhook 설정:
    - Dashboard > Settings > Chat > Webhooks
    - URL: https://your-domain.com/webhook/sendbird/chat
    - Events: message:send
    """
    try:
        logger.info("=" * 80)
        logger.info("🔔 [WEBHOOK-DEBUG] Sendbird webhook received!")

        # JSON 파싱 에러 처리
        try:
            payload = await request.json()
            logger.info(f"📦 [WEBHOOK-DEBUG] Payload: {payload}")
        except Exception as json_error:
            logger.warning(f"⚠️ Invalid JSON in webhook request: {str(json_error)}")
            return {"status": "ignored", "reason": "invalid_json"}

        # 빈 payload 처리
        if not payload:
            logger.warning("⚠️ Empty payload received")
            return {"status": "ignored", "reason": "empty_payload"}

        # 웹훅 카테고리 확인
        category = payload.get("category")
        logger.info(f"📂 [WEBHOOK-DEBUG] Category: {category}")

        if category == "group_channel:message_send":
            logger.info("✅ [WEBHOOK-DEBUG] Processing message_send event...")
            # 메시지 전송 이벤트
            await handle_message_send(payload, background_tasks)
        else:
            logger.warning(f"⚠️ [WEBHOOK-DEBUG] Unhandled category: {category}")

        logger.info("=" * 80)
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        logger.error(f"   Stack trace:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def handle_message_send(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """메시지 전송 이벤트 처리"""
    try:
        logger.info("📨 [WEBHOOK-DEBUG] Parsing message payload...")

        # 페이로드 파싱
        channel_url = payload.get("channel", {}).get("channel_url")
        sender = payload.get("sender", {})
        sender_id = sender.get("user_id")
        message_payload = payload.get("payload", {})
        message = message_payload.get("message", "")

        # 메시지 데이터에서 persona_context 추출 (프론트엔드에서 전송)
        persona_context = None
        message_data = message_payload.get("data")
        if message_data:
            try:
                import json
                data_dict = json.loads(message_data) if isinstance(message_data, str) else message_data
                persona_context = data_dict.get("persona_context")
                if persona_context:
                    logger.info(f"📋 [WEBHOOK-DEBUG] Persona context from message data: {persona_context[:100]}...")
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse message data: {e}")

        logger.info(f"   Channel URL: {channel_url}")
        logger.info(f"   Sender ID: {sender_id}")
        logger.info(f"   Message: {message}")
        logger.info(f"   Has persona context: {persona_context is not None}")
        logger.info(f"   AI User ID: {SendbirdConfig.AI_USER_ID}")

        # AI 자신의 메시지는 무시
        if sender_id == SendbirdConfig.AI_USER_ID:
            logger.info("⏭️  [WEBHOOK-DEBUG] Ignoring AI's own message")
            return

        logger.info(f"✅ [WEBHOOK-DEBUG] Processing user message from {sender_id}: {message}")

        # 메모리에 추가
        memory_service.add_message(sender_id, "user", message)
        logger.info("💾 [WEBHOOK-DEBUG] Message added to memory")

        # 백그라운드에서 응답 생성 및 전송
        logger.info("🚀 [WEBHOOK-DEBUG] Adding background task for response generation...")
        background_tasks.add_task(
            process_and_respond,
            channel_url,
            sender_id,
            message,
            persona_context
        )
        logger.info("✅ [WEBHOOK-DEBUG] Background task added successfully")

    except Exception as e:
        logger.error(f"❌ Message handling error: {str(e)}")
        logger.error(f"   Stack trace:", exc_info=True)


async def process_and_respond(
    channel_url: str,
    user_id: str,
    message: str,
    persona_context: Optional[str] = None
):
    """메시지 처리 및 응답"""
    from app.config.db import SessionLocal
    from app.services.appliance_rule_engine import appliance_rule_engine
    from app.services.weather_service import weather_service
    from app.services.hrv_service import hrv_service
    from app.services.appliance_control_service import appliance_control_service
    from app.models.user import User
    from app.models.location import UserLocation
    from app.utils.user_utils import get_user_by_identifier
    import os

    db = SessionLocal()

    try:
        logger.info("=" * 80)
        logger.info("🤖 [RESPONSE-DEBUG] Starting AI response generation...")
        logger.info(f"   Sendbird User ID: {user_id}")
        logger.info(f"   Message: {message}")
        logger.info(f"   Channel: {channel_url}")

        # Sendbird user_id(email 또는 UUID)를 실제 DB User로 변환
        actual_user = get_user_by_identifier(db, user_id)

        if not actual_user:
            logger.error(f"❌ [USER-MAPPING] User not found: {user_id}")
            # 에러 메시지 전송
            await chat_client.send_message(
                channel_url=channel_url,
                message="죄송해요, 사용자 정보를 찾을 수 없습니다. 다시 로그인해주세요.",
                user_id=user_id
            )
            return

        actual_user_id = str(actual_user.id)
        logger.info(f"✅ [USER-MAPPING] Mapped Sendbird user {user_id} to DB user {actual_user_id} ({actual_user.email})")

        # 대화 히스토리 조회
        history = memory_service.get_history(user_id)
        logger.info(f"📚 [RESPONSE-DEBUG] Retrieved {len(history)} messages from history")

        # 장기 메모리 조회 (사용자 정보, 선호도 등)
        long_term = memory_service.get_long_term_memory(user_id)
        logger.info(f"💭 [RESPONSE-DEBUG] Long-term memory: {long_term.get('persona', 'default')}")

        # 페르소나 로드
        # 1순위: 프론트엔드에서 전송한 persona_context 사용
        # 2순위: Supabase에서 조회
        persona = None
        if persona_context:
            # 프론트엔드에서 받은 persona_context를 LLM 형식으로 변환
            persona = {
                "nickname": "User Selected Persona",
                "description": persona_context
            }
            logger.info(f"✅ [RESPONSE-DEBUG] Using persona context from frontend: {persona_context[:100]}...")
        elif supabase_persona_service.is_available():
            # Supabase에서 페르소나 조회
            # NOTE: Supabase는 Supabase Auth UUID를 사용하지만, 현재는 이메일로 시도
            # 향후 iOS 앱에서 FastAPI user_id를 사용하도록 수정 필요
            # 임시: 이메일로 조회 시도 (조회 실패 시 persona_context 사용)
            logger.info(f"🔍 [PERSONA-DEBUG] Attempting to query Supabase with email: {actual_user.email}")
            selected_personas = supabase_persona_service.get_user_selected_personas(actual_user.email, limit=1)
            if selected_personas and len(selected_personas) > 0:
                persona_id = selected_personas[0].get("persona_id")
                if persona_id:
                    persona = supabase_persona_service.get_persona_for_llm(persona_id)
                    if persona:
                        logger.info(f"✅ [RESPONSE-DEBUG] Loaded persona from Supabase: {persona['nickname']}")
                    else:
                        logger.warning(f"⚠️ [RESPONSE-DEBUG] Persona not found in Supabase: {persona_id}")
            else:
                logger.info("ℹ️ [RESPONSE-DEBUG] No selected persona for user")
        else:
            logger.warning("⚠️ [RESPONSE-DEBUG] No persona context and Supabase not available")

        # 1. 의도 파싱
        logger.info("🧠 [RESPONSE-DEBUG] Parsing user intent...")
        intent_result = await llm_service.parse_user_intent(
            user_message=message,
            context=None
        )

        intent_type = intent_result.get("intent_type")
        needs_control = intent_result.get("needs_control", False)
        logger.info(f"📝 [RESPONSE-DEBUG] Intent: {intent_type}, needs_control: {needs_control}")

        # environment_complaint나 appliance_request는 무조건 제어 필요
        if intent_type in ["environment_complaint", "appliance_request"]:
            needs_control = True

        # 현재 가전 상태 조회 (실제 DB user_id 사용)
        appliance_states = appliance_control_service.get_appliance_status(
            db=db,
            user_id=actual_user_id
        )

        # 2. 가전 제어가 필요 없는 경우 (일반 대화)
        if intent_type == "general_chat" or not needs_control:
            logger.info("💬 [RESPONSE-DEBUG] General chat - generating normal response...")
            response = await llm_service.generate_response(
                user_message=message,
                conversation_history=history,
                persona=persona,
                appliance_states=appliance_states,
                context={
                    "user_id": user_id,
                    "channel_url": channel_url
                }
            )

            action = response.get("action", "NONE")
            response_text = response.get("response", "")
            logger.info(f"✅ [RESPONSE-DEBUG] LLM response generated!")
            logger.info(f"   Action: {action}")
            logger.info(f"   Response: {response_text[:100]}...")

            # 메모리에 AI 응답 추가
            memory_service.add_message(user_id, "assistant", response_text)
            logger.info("💾 [RESPONSE-DEBUG] AI response saved to memory")

            # 액션 처리
            if action == LLMAction.NONE:
                # 일반 텍스트 응답
                logger.info("📤 [RESPONSE-DEBUG] Sending text response via Sendbird...")
                await chat_client.send_message(
                    channel_url=channel_url,
                    message=response_text,
                    user_id=user_id
                )
                logger.info(f"✅ [RESPONSE-DEBUG] Text response sent to {user_id} successfully!")

            elif action == LLMAction.CALL:
                # 전화 걸기
                await chat_client.send_message(
                    channel_url=channel_url,
                    message=response_text,
                    user_id=user_id
                )
                await calls_client.make_call(
                    caller_id=SendbirdConfig.AI_USER_ID,
                    callee_id=user_id,
                    call_type="voice"
                )
                logger.info(f"📞 Call initiated to {user_id}")

            elif action == LLMAction.AUTO_CALL:
                # 자동 전화
                message_to_user = response.get("message_to_user", response_text)
                await chat_client.send_message(
                    channel_url=channel_url,
                    message=message_to_user,
                    user_id=user_id
                )
                await calls_client.make_call(
                    caller_id=SendbirdConfig.AI_USER_ID,
                    callee_id=user_id,
                    call_type="voice"
                )
                logger.info(f"📞 Auto-call initiated to {user_id}")

            logger.info("=" * 80)
            return

        # 3. 가전 제어가 필요한 경우
        logger.info("🏠 [RESPONSE-DEBUG] Appliance control needed - getting context...")

        # 사용자 위치 정보 조회 (actual_user는 이미 조회됨)
        user_location = db.query(UserLocation).filter(UserLocation.user_id == actual_user.id).first()
        home_lat = user_location.home_latitude if user_location else 37.5665
        home_lng = user_location.home_longitude if user_location else 126.9780

        # 날씨 정보 조회
        logger.info("🌤️ [RESPONSE-DEBUG] Fetching weather data...")
        weather_data = await weather_service.get_combined_weather(
            db=db,
            latitude=home_lat,
            longitude=home_lng,
            sido_name=os.getenv("DEFAULT_SIDO_NAME", "서울")
        )
        logger.info(f"   Temperature: {weather_data.get('temperature')}°C")
        logger.info(f"   Humidity: {weather_data.get('humidity')}%")
        logger.info(f"   PM10: {weather_data.get('pm10')} ㎍/㎥")

        # 피로도 조회 (DB user UUID 사용)
        logger.info("💪 [RESPONSE-DEBUG] Fetching fatigue level...")
        fatigue_level = hrv_service.get_latest_fatigue_level(db, actual_user.id)
        if fatigue_level is None:
            fatigue_level = 2
            logger.warning(f"⚠️ No fatigue level, using default: {fatigue_level}")
        else:
            logger.info(f"   Fatigue level: {fatigue_level}")

        # 피로도 기반 가전 제어 추천 생성 (자동 조건 기반) - 실제 DB user_id 사용
        logger.info("🔧 [RESPONSE-DEBUG] Generating appliance recommendations based on fatigue...")
        recommendations = appliance_rule_engine.get_appliances_to_control(
            db=db,
            user_id=actual_user_id,
            weather_data=weather_data,
            fatigue_level=fatigue_level
        )

        # 사용자가 직접 불편을 표현한 경우, LLM이 판단하도록 함
        # 조건 테이블에 맞지 않더라도 사용자 요청을 우선
        if not recommendations:
            logger.info("ℹ️ [RESPONSE-DEBUG] No rule-based recommendations, asking LLM to suggest based on user message...")
            # LLM에게 사용자 메시지와 현재 가전 상태를 주고 제안 요청
            response_result = await llm_service.generate_user_request_suggestion(
                user_message=message,
                appliance_states=appliance_states,
                weather=weather_data,
                fatigue_level=fatigue_level,
                persona=persona,
                conversation_history=history
            )

            response_text = response_result.get("response", "")
            suggested_appliances = response_result.get("appliances", [])

            if not suggested_appliances:
                # LLM도 제안이 없으면 일반 응답
                logger.info("ℹ️ [RESPONSE-DEBUG] LLM also suggests no changes")
                memory_service.add_message(user_id, "assistant", response_text)
                await chat_client.send_message(
                    channel_url=channel_url,
                    message=response_text,
                    user_id=user_id
                )
                logger.info("=" * 80)
                return

            # LLM 제안을 recommendations로 사용
            recommendations = suggested_appliances
            logger.info(f"✅ [RESPONSE-DEBUG] LLM suggested {len(recommendations)} appliances")
        else:
            # 자연어 제안 생성 (피로도 기반 설정값 포함)
            logger.info(f"💡 [RESPONSE-DEBUG] Generating suggestion message for {len(recommendations)} appliances...")
            response_text = await llm_service.generate_appliance_suggestion(
                appliances=recommendations,
                weather=weather_data,
                fatigue_level=fatigue_level,
                user_message=message,
                persona=persona,
                appliance_states=appliance_states,
                conversation_history=history
            )

        logger.info(f"✅ [RESPONSE-DEBUG] Suggestion generated!")
        logger.info(f"   Response: {response_text[:100]}...")
        logger.info(f"   Recommendations: {[r['appliance_type'] + ' (' + str(r.get('settings', {})) + ')' for r in recommendations]}")

        # 메모리에 AI 응답 추가
        memory_service.add_message(user_id, "assistant", response_text)
        logger.info("💾 [RESPONSE-DEBUG] AI response saved to memory")

        # 가전 제안을 메타데이터로 구성
        import json
        message_metadata = {
            "appliance_suggestions": recommendations,
            "weather": {
                "temperature": weather_data.get("temperature"),
                "humidity": weather_data.get("humidity"),
                "pm10": weather_data.get("pm10")
            },
            "fatigue_level": fatigue_level
        }

        # Sendbird로 메시지 전송 (메타데이터 포함)
        logger.info("📤 [RESPONSE-DEBUG] Sending appliance suggestion via Sendbird...")
        await chat_client.send_message(
            channel_url=channel_url,
            message=response_text,
            user_id=user_id,
            data=json.dumps(message_metadata),
            custom_type="appliance_suggestion"
        )
        logger.info(f"✅ [RESPONSE-DEBUG] Appliance suggestion sent to {user_id} with metadata!")
        logger.info(f"   Metadata: {len(recommendations)} appliances")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Process and respond error: {str(e)}")
        logger.error(f"   Stack trace:", exc_info=True)

        # 에러 메시지 전송
        try:
            await chat_client.send_message(
                channel_url=channel_url,
                message="죄송해요, 일시적인 오류가 발생했어요. 잠시 후 다시 시도해주세요.",
                user_id=user_id
            )
        except:
            pass
    finally:
        db.close()


@router.post("/calls")
async def sendbird_calls_webhook(request: Request):
    """
    Sendbird Calls 웹훅 수신

    Webhook 설정:
    - Dashboard > Calls > Settings > Webhooks
    - Events: call.ended, call.established 등
    """
    try:
        # JSON 파싱 에러 처리
        try:
            payload = await request.json()
        except Exception as json_error:
            logger.warning(f"⚠️ Invalid JSON in calls webhook request: {str(json_error)}")
            return {"status": "ignored", "reason": "invalid_json"}

        # 빈 payload 처리
        if not payload:
            logger.warning("⚠️ Empty payload received in calls webhook")
            return {"status": "ignored", "reason": "empty_payload"}

        event_type = payload.get("type")
        call_id = payload.get("call_id")

        logger.info(f"📞 Calls webhook: {event_type} - {call_id}")

        # 통화 종료 시 요약 생성 등
        if event_type == "call.ended":
            await handle_call_ended(payload)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Calls webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_call_ended(payload: Dict[str, Any]):
    """통화 종료 처리"""
    try:
        call_id = payload.get("call_id")
        duration = payload.get("duration", 0)
        
        # TODO: 통화 내용 요약, 메모리 업데이트 등
        logger.info(f"📴 Call ended: {call_id}, duration: {duration}s")
    
    except Exception as e:
        logger.error(f"❌ Call ended handling error: {str(e)}")


