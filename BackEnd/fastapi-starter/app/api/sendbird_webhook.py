"""
Sendbird Webhook API
채팅 메시지 수신 및 처리
"""
import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional

from app.services.sendbird_client import SendbirdChatClient
from app.services.llm_service import llm_service, memory_service, LLMAction
from app.services.supabase_service import supabase_persona_service
from app.config.sendbird import SendbirdConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook/sendbird", tags=["Sendbird Webhook"])

# 클라이언트 초기화
chat_client = SendbirdChatClient()


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

        # 현재 가전 상태 조회 (실제 DB user_id 사용)
        appliance_states = appliance_control_service.get_appliance_status(
            db=db,
            user_id=actual_user_id
        )

        # 0. 대기 중인 가전 제안 확인 (시나리오 1에서 생성된 제안)
        pending_suggestion = long_term.get("pending_appliance_suggestion")

        if pending_suggestion:
            logger.info("🔔 [APPROVAL-CHECK] Found pending appliance suggestion!")
            logger.info(f"   Appliances: {[a['appliance_type'] for a in pending_suggestion.get('appliances', [])]}")

            # LLM으로 승인/거절 판단
            logger.info("🧠 [APPROVAL-CHECK] Checking if message is approval...")
            approval_result = await llm_service.detect_modification(
                original_plan={"recommendations": pending_suggestion.get("appliances", [])},
                user_response=message
            )

            approved = approval_result.get("approved", False)
            has_modification = approval_result.get("has_modification", False)
            modifications = approval_result.get("modifications", {})

            logger.info(f"📝 [APPROVAL-CHECK] Approved: {approved}, Has modification: {has_modification}")

            if approved:
                # 승인됨 - 가전 제어 실행
                logger.info("✅ [APPLIANCE-CONTROL] User approved! Executing appliance controls...")

                execution_results = []
                recommendations = pending_suggestion.get("appliances", [])
                fatigue_level = pending_suggestion.get("fatigue_level", 2)

                # 한글 모드명을 영문으로 변환하는 매핑
                MODE_TRANSLATION = {
                    "냉방": "cool",
                    "난방": "heat",
                    "송풍": "fan",
                    "제습": "dry",
                    "자동": "auto"
                }

                for rec in recommendations:
                    appliance_type = rec["appliance_type"]
                    action = rec.get("action", "on")
                    settings = rec.get("settings", {}).copy()  # 원본 보존을 위해 복사

                    # 수정 사항 적용
                    if has_modification and appliance_type in modifications:
                        user_modifications = modifications[appliance_type].copy()

                        # 에어컨 모드 변경 시 한글→영문 변환 및 해당 모드 설정 가져오기
                        if appliance_type == "에어컨" and "mode" in user_modifications:
                            korean_mode = user_modifications["mode"]
                            if korean_mode in MODE_TRANSLATION:
                                english_mode = MODE_TRANSLATION[korean_mode]
                                user_modifications["mode"] = english_mode
                                logger.info(f"🔄 [MODE-TRANSLATION] '{korean_mode}' → '{english_mode}'")

                                # 해당 모드의 기본 설정을 UserAppliancePreference에서 가져오기
                                from app.models.appliance import UserAppliancePreference
                                from uuid import UUID

                                try:
                                    preference = db.query(UserAppliancePreference).filter(
                                        UserAppliancePreference.user_id == UUID(actual_user_id),
                                        UserAppliancePreference.fatigue_level == fatigue_level,
                                        UserAppliancePreference.appliance_type == appliance_type
                                    ).first()

                                    if preference and preference.settings_json:
                                        # 모드별 설정이 있는지 확인 (예: {"cool": {...}, "heat": {...}})
                                        if isinstance(preference.settings_json, dict):
                                            if english_mode in preference.settings_json:
                                                # 해당 모드의 전체 설정 가져오기
                                                mode_settings = preference.settings_json[english_mode]
                                                settings = mode_settings.copy()
                                                logger.info(f"✨ [MODE-CHANGE] Loaded settings for '{english_mode}' mode: {settings}")
                                            elif "mode" in preference.settings_json:
                                                # 단일 설정 구조인 경우
                                                settings = preference.settings_json.copy()
                                                settings["mode"] = english_mode
                                            else:
                                                # 기본 설정에 모드만 추가
                                                settings["mode"] = english_mode
                                except Exception as pref_error:
                                    logger.warning(f"⚠️ Failed to load preference for mode change: {pref_error}")
                                    # Fallback: 온도만 유지하고 모드 변경
                                    if "target_temp_c" in settings:
                                        temp = settings["target_temp_c"]
                                        settings = {"mode": english_mode, "target_temp_c": temp}
                                    else:
                                        settings = {"mode": english_mode}

                        # 다른 수정사항 적용 (온도 등)
                        for key, value in user_modifications.items():
                            if key != "mode" or appliance_type != "에어컨":  # 에어컨 모드는 위에서 이미 처리
                                settings[key] = value

                        logger.info(f"🔧 [APPLIANCE-CONTROL] Modified {appliance_type}: {settings}")

                    # 가전 제어 실행
                    try:
                        result = appliance_control_service.execute_command(
                            db=db,
                            user_id=actual_user_id,
                            appliance_type=appliance_type,
                            action=action,
                            settings=settings,
                            triggered_by="scenario1_approved"
                        )

                        # 실행 결과 확인
                        if result.get("success", False):
                            execution_results.append({
                                "appliance": appliance_type,
                                "action": action,
                                "settings": settings,
                                "status": "success"
                            })
                            logger.info(f"✅ [APPLIANCE-CONTROL] {appliance_type} {action} success")
                        else:
                            execution_results.append({
                                "appliance": appliance_type,
                                "action": action,
                                "status": "error",
                                "error": result.get("error_message", "Unknown error")
                            })
                            logger.error(f"❌ [APPLIANCE-CONTROL] {appliance_type} {action} failed: {result.get('error_message')}")
                            continue  # 실패한 경우 선호 세팅 학습 건너뛰기

                        # 선호 세팅 학습
                        try:
                            from app.models.appliance import UserAppliancePreference
                            from uuid import UUID

                            preference = db.query(UserAppliancePreference).filter(
                                UserAppliancePreference.user_id == UUID(actual_user_id),
                                UserAppliancePreference.fatigue_level == fatigue_level,
                                UserAppliancePreference.appliance_type == appliance_type
                            ).first()

                            if action == "on" and settings:
                                if preference:
                                    preference.settings_json = settings
                                    preference.is_learned = True  # ✅ 사용자가 승인했으므로 학습됨으로 표시
                                    logger.info(f"📝 [LEARNING] Updated preference (is_learned=True) for {appliance_type}")
                                else:
                                    new_preference = UserAppliancePreference(
                                        user_id=UUID(actual_user_id),
                                        fatigue_level=fatigue_level,
                                        appliance_type=appliance_type,
                                        settings_json=settings,
                                        is_learned=True  # ✅ 사용자가 승인했으므로 학습됨으로 표시
                                    )
                                    db.add(new_preference)
                                    logger.info(f"✨ [LEARNING] Created preference (is_learned=True) for {appliance_type}")
                                db.commit()
                        except Exception as pref_error:
                            logger.error(f"⚠️ [LEARNING] Failed to save preference: {str(pref_error)}")
                            db.rollback()

                    except Exception as e:
                        execution_results.append({
                            "appliance": appliance_type,
                            "action": action,
                            "status": "error",
                            "error": str(e)
                        })
                        logger.error(f"❌ [APPLIANCE-CONTROL] {appliance_type} error: {str(e)}")

                # LLM을 사용해서 자연스러운 실행 결과 메시지 생성
                success_count = sum(1 for r in execution_results if r["status"] == "success")

                if success_count > 0:
                    # 성공한 가전 정보 수집
                    success_appliances = []
                    for r in execution_results:
                        if r["status"] == "success":
                            success_appliances.append({
                                "appliance_type": r["appliance"],
                                "action": r["action"],
                                "settings": r.get("settings", {})
                            })

                    # LLM으로 자연스러운 메시지 생성
                    try:
                        # 페르소나 정보 (이미 로드되어 있음)
                        response_text = await llm_service.generate_appliance_execution_result(
                            appliances=success_appliances,
                            has_modification=has_modification,
                            persona=persona
                        )
                    except Exception as llm_error:
                        logger.warning(f"⚠️ LLM response generation failed, using fallback: {llm_error}")
                        # Fallback: 간단한 메시지
                        if has_modification:
                            response_text = "수정하신 내용으로 제어했어요!"
                        else:
                            response_text = "알겠습니다. 제어했어요!"
                else:
                    response_text = "가전 제어에 실패했습니다. 다시 시도해주세요."

                # 메모리 업데이트
                memory_service.add_message(user_id, "assistant", response_text)
                memory_service.update_long_term_memory(user_id, "pending_appliance_suggestion", None)
                logger.info("💾 [APPLIANCE-CONTROL] Cleared pending suggestion from memory")

                # 응답 전송
                await chat_client.send_message(
                    channel_url=channel_url,
                    message=response_text,
                    user_id=user_id
                )
                logger.info(f"✅ [APPLIANCE-CONTROL] Execution result sent to {user_id}")
                logger.info("=" * 80)
                return

            elif not approved:
                # 거절됨 - 시나리오 1
                logger.info("❌ [APPROVAL-CHECK] User declined appliance control (Scenario 1)")

                # ✅ 기각된 가전들의 ApplianceConditionRule 조건 임계값 수정
                from app.models.appliance import ApplianceConditionRule
                from uuid import UUID

                if pending_suggestion and pending_suggestion.get("appliances"):
                    fatigue_level = pending_suggestion.get("fatigue_level")
                    weather_data = pending_suggestion.get("weather", {})

                    # 현재 날씨 정보
                    current_temp = weather_data.get("temperature")
                    current_humidity = weather_data.get("humidity")
                    current_pm10 = weather_data.get("pm10")

                    for appliance_info in pending_suggestion["appliances"]:
                        appliance_type = appliance_info.get("appliance_type")

                        # 해당 가전의 조건 규칙 조회 및 임계값 수정
                        try:
                            rules = db.query(ApplianceConditionRule).filter(
                                ApplianceConditionRule.user_id == UUID(actual_user_id),
                                ApplianceConditionRule.fatigue_level == fatigue_level,
                                ApplianceConditionRule.appliance_type == appliance_type
                            ).all()

                            for rule in rules:
                                condition = rule.condition_json.copy()
                                updated = False

                                # 온도 기반 조건 수정
                                if "temp_threshold" in condition and current_temp is not None:
                                    old_threshold = condition["temp_threshold"]
                                    margin = 3  # 3도 마진

                                    if condition.get("operator") == ">=":
                                        new_threshold = max(current_temp + margin, old_threshold + margin)
                                        condition["temp_threshold"] = new_threshold
                                        updated = True
                                        logger.info(f"📈 [LEARNING] Updated temp threshold (>=): {old_threshold}°C → {new_threshold}°C for {appliance_type}")
                                    elif condition.get("operator") == "<=":
                                        new_threshold = min(current_temp - margin, old_threshold - margin)
                                        condition["temp_threshold"] = new_threshold
                                        updated = True
                                        logger.info(f"📉 [LEARNING] Updated temp threshold (<=): {old_threshold}°C → {new_threshold}°C for {appliance_type}")

                                # 습도 기반 조건 수정
                                if "humidity_threshold" in condition and current_humidity is not None:
                                    old_threshold = condition["humidity_threshold"]
                                    margin = 5  # 5% 마진

                                    if condition.get("operator") == ">=":
                                        new_threshold = max(current_humidity + margin, old_threshold + margin)
                                        condition["humidity_threshold"] = new_threshold
                                        updated = True
                                        logger.info(f"📈 [LEARNING] Updated humidity threshold (>=): {old_threshold}% → {new_threshold}% for {appliance_type}")
                                    elif condition.get("operator") == "<=":
                                        new_threshold = min(current_humidity - margin, old_threshold - margin)
                                        condition["humidity_threshold"] = new_threshold
                                        updated = True
                                        logger.info(f"📉 [LEARNING] Updated humidity threshold (<=): {old_threshold}% → {new_threshold}% for {appliance_type}")

                                # 미세먼지 기반 조건 수정
                                if "pm10_threshold" in condition and current_pm10 is not None:
                                    old_threshold = condition["pm10_threshold"]
                                    margin = 10  # 10㎍/㎥ 마진

                                    if condition.get("operator") == ">=":
                                        new_threshold = max(current_pm10 + margin, old_threshold + margin)
                                        condition["pm10_threshold"] = new_threshold
                                        updated = True
                                        logger.info(f"📈 [LEARNING] Updated pm10 threshold: {old_threshold} → {new_threshold} for {appliance_type}")

                                if updated:
                                    rule.condition_json = condition

                            db.commit()
                            logger.info(f"✅ [LEARNING] Updated condition thresholds for {appliance_type} (rejected in scenario1)")
                        except Exception as e:
                            logger.error(f"⚠️ [LEARNING] Failed to update condition for {appliance_type}: {str(e)}")
                            db.rollback()

                response_text = "알겠습니다. 필요하시면 언제든 말씀해주세요."
                memory_service.add_message(user_id, "assistant", response_text)
                memory_service.update_long_term_memory(user_id, "pending_appliance_suggestion", None)

                await chat_client.send_message(
                    channel_url=channel_url,
                    message=response_text,
                    user_id=user_id
                )
                logger.info("=" * 80)
                return

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

        # 2. 가전 제어가 필요 없는 경우 (일반 대화)
        if intent_type == "general_chat" or not needs_control:
            logger.info("💬 [RESPONSE-DEBUG] General chat - generating normal response...")

            # 날씨 정보 조회 (일반 대화에도 컨텍스트 제공)
            user_location = db.query(UserLocation).filter(UserLocation.user_id == actual_user.id).first()
            home_lat = user_location.home_latitude if user_location and user_location.home_latitude else 37.5665
            home_lng = user_location.home_longitude if user_location and user_location.home_longitude else 126.9780

            # 위치가 0,0이면 서울 기본 위치 사용
            if home_lat == 0.0 or home_lng == 0.0:
                logger.warning(f"⚠️ Invalid location (0,0), using default Seoul location")
                home_lat = 37.5665
                home_lng = 126.9780

            weather_data = await weather_service.get_combined_weather(
                db=db,
                latitude=home_lat,
                longitude=home_lng,
                sido_name=os.getenv("DEFAULT_SIDO_NAME", "서울")
            )

            # 피로도 정보도 제공
            fatigue_level = hrv_service.get_latest_fatigue_level(db, actual_user.id)

            # 컨텍스트 구성
            context = {
                "weather": weather_data,
                "fatigue_level": fatigue_level,
                "location": {
                    "latitude": home_lat,
                    "longitude": home_lng
                },
                "user_id": user_id,
                "channel_url": channel_url
            }

            response = await llm_service.generate_response(
                user_message=message,
                conversation_history=history,
                persona=persona,
                appliance_states=appliance_states,
                context=context
            )

            action = response.get("action", "NONE")
            response_text = response.get("response", "")
            logger.info(f"✅ [RESPONSE-DEBUG] LLM response generated!")
            logger.info(f"   Action: {action}")
            logger.info(f"   Response: {response_text[:100]}...")

            # 메모리에 AI 응답 추가
            memory_service.add_message(user_id, "assistant", response_text)
            logger.info("💾 [RESPONSE-DEBUG] AI response saved to memory")

            # 텍스트 응답 전송 (전화 기능 제거됨)
            logger.info("📤 [RESPONSE-DEBUG] Sending text response via Sendbird...")
            await chat_client.send_message(
                channel_url=channel_url,
                message=response_text,
                user_id=user_id
            )
            logger.info(f"✅ [RESPONSE-DEBUG] Text response sent to {user_id} successfully!")
            logger.info("=" * 80)
            return

        # 3. 가전 제어가 필요한 경우
        logger.info("🏠 [RESPONSE-DEBUG] Appliance control needed - getting context...")

        # 사용자 위치 정보 조회 (actual_user는 이미 조회됨)
        user_location = db.query(UserLocation).filter(UserLocation.user_id == actual_user.id).first()
        home_lat = user_location.home_latitude if user_location and user_location.home_latitude else 37.5665
        home_lng = user_location.home_longitude if user_location and user_location.home_longitude else 126.9780

        # 위치가 0,0이면 서울 기본 위치 사용
        if home_lat == 0.0 or home_lng == 0.0:
            logger.warning(f"⚠️ Invalid location (0,0), using default Seoul location")
            home_lat = 37.5665
            home_lng = 126.9780

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

        # 사용자가 특정 가전을 명시적으로 요청했는지 확인
        appliance_keywords = ["에어컨", "조명", "공기청정기", "제습기", "가습기", "TV"]
        user_mentioned_appliance = any(keyword in message for keyword in appliance_keywords)

        # 피로도 기반 가전 제어 추천 생성 (자동 조건 기반) - 실제 DB user_id 사용
        logger.info("🔧 [RESPONSE-DEBUG] Generating appliance recommendations based on fatigue...")
        recommendations = appliance_rule_engine.get_appliances_to_control(
            db=db,
            user_id=actual_user_id,
            weather_data=weather_data,
            fatigue_level=fatigue_level
        )

        # 사용자가 직접 불편을 표현하거나 특정 가전을 요청한 경우, LLM이 판단하도록 함
        # 조건 테이블에 맞지 않더라도 사용자 요청을 우선
        if not recommendations or user_mentioned_appliance:
            if user_mentioned_appliance:
                logger.info(f"🎯 [RESPONSE-DEBUG] User mentioned specific appliance, asking LLM to suggest based on user message...")
            else:
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

        # 가전 제안을 pending으로 저장 (사용자 승인 대기)
        memory_service.update_long_term_memory(user_id, "pending_appliance_suggestion", {
            "appliances": recommendations,
            "fatigue_level": fatigue_level,
            "weather": weather_data
        })
        logger.info("💾 [RESPONSE-DEBUG] Saved pending appliance suggestion for approval")

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

        # 🔍 전체 페이로드 로깅 (디버깅용)
        logger.info(f"📦 [CALLS-WEBHOOK] Full payload: {payload}")

        # Sendbird Calls 웹훅 페이로드 구조
        category = payload.get("category")  # "direct_call:dial", "direct_call:accept", "direct_call:end"
        direct_call = payload.get("direct_call", {})
        call_id = direct_call.get("call_id")

        logger.info(f"📞 Calls webhook: {category} - {call_id}")

        # 이벤트별 처리
        if category == "direct_call:dial":
            # 전화 발신 시
            await handle_call_dialing(payload)
        elif category == "direct_call:accept":
            # 전화 수락 시
            await handle_call_established(payload)
        elif category == "direct_call:end":
            # 통화 종료 시
            await handle_call_ended(payload)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Calls webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_call_ended(payload: Dict[str, Any]):
    """
    통화 종료 처리

    통화 종료 시 수행되는 작업:
    1. 통화 기록 로깅
    2. 통화 시간 기록
    3. 메모리 서비스에 통화 이벤트 저장
    4. 필요 시 통화 내용 요약 (향후 구현)
    """
    from app.config.db import SessionLocal

    db = SessionLocal()

    try:
        # 페이로드에서 통화 정보 추출
        direct_call = payload.get("direct_call", {})
        call_id = direct_call.get("call_id")
        duration = direct_call.get("duration", 0)
        caller_id = direct_call.get("caller_id")
        callee_id = direct_call.get("callee_id")
        end_result = direct_call.get("end_result")  # completed, canceled, declined, timed_out 등
        ended_at = direct_call.get("ended_at")

        logger.info(f"📴 Call ended: {call_id}")
        logger.info(f"   Caller: {caller_id}")
        logger.info(f"   Callee: {callee_id}")
        logger.info(f"   Duration: {duration}s")
        logger.info(f"   End result: {end_result}")

        # 통화 기록을 메모리 서비스에 저장
        if caller_id and callee_id:
            # AI가 발신자인 경우와 수신자인 경우 구분
            user_id = callee_id if caller_id == SendbirdConfig.AI_USER_ID else caller_id

            # 통화 이벤트 메시지 생성
            call_summary = f"통화 종료 (시간: {duration}초, 결과: {end_result})"

            # 메모리에 통화 기록 추가
            memory_service.add_message(user_id, "system", call_summary)
            logger.info(f"💾 Call record saved to memory for user: {user_id}")

            # 장기 메모리에 통화 통계 업데이트 (선택적)
            long_term = memory_service.get_long_term_memory(user_id)
            call_count = long_term.get("call_count", 0) + 1
            total_call_duration = long_term.get("total_call_duration", 0) + duration

            # 각 키-값 쌍을 개별적으로 업데이트
            memory_service.update_long_term_memory(user_id, "call_count", call_count)
            memory_service.update_long_term_memory(user_id, "total_call_duration", total_call_duration)
            memory_service.update_long_term_memory(user_id, "last_call_ended_at", ended_at)

            logger.info(f"📊 Call statistics updated: {call_count} calls, {total_call_duration}s total")

        # TODO: 향후 구현 사항
        # 1. DB에 통화 기록 영구 저장 (CallHistory 테이블)
        # 2. 통화 내용 녹음이 있는 경우 STT 처리
        # 3. AI 통화 내용 요약 생성
        # 4. 통화 중 언급된 가전 제어 요청 처리

    except Exception as e:
        logger.error(f"❌ Call ended handling error: {str(e)}")
        logger.error(f"   Payload: {payload}")
    finally:
        db.close()


async def handle_call_dialing(payload: Dict[str, Any]):
    """
    전화 발신 처리

    NOTE: Sendbird Calls는 서버에서 통화를 수락하는 API를 제공하지 않습니다.
    통화 수락은 클라이언트 SDK를 통해서만 가능합니다.

    현재는 통화 이벤트를 로깅하고 메모리에 기록만 합니다.
    실제 통화 수락은 iOS 앱에서 처리해야 합니다.
    """
    try:
        direct_call = payload.get("direct_call", {})
        call_id = direct_call.get("call_id")
        caller_id = direct_call.get("caller_id")
        callee_id = direct_call.get("callee_id")

        logger.info(f"📞 [CALL-INCOMING] Call received!")
        logger.info(f"   Call ID: {call_id}")
        logger.info(f"   Caller: {caller_id}")
        logger.info(f"   Callee: {callee_id}")
        logger.info(f"   AI User ID: {SendbirdConfig.AI_USER_ID}")

        # AI assistant가 수신자인 경우
        if callee_id == SendbirdConfig.AI_USER_ID:
            logger.info(f"🤖 [CALL-INCOMING] AI assistant receiving call from {caller_id}")

            # 통화 이벤트를 메모리에 기록
            memory_service.add_message(
                caller_id,
                "system",
                f"전화 수신 시작 (Call ID: {call_id})"
            )

            # TODO: 실제 AI 통화 수락 로직은 별도의 WebRTC 클라이언트가 필요
            # 현재는 iOS 앱에서 AI가 자동으로 응답하도록 구현 필요
            logger.info(f"ℹ️ [CALL-INCOMING] Call must be accepted by iOS client, not server")
        else:
            logger.info(f"ℹ️ [CALL-INCOMING] Not for AI assistant, ignoring")

    except Exception as e:
        logger.error(f"❌ Incoming call handling error: {str(e)}")
        logger.error(f"   Payload: {payload}")


async def handle_call_established(payload: Dict[str, Any]):
    """
    통화 연결됨 처리

    통화가 정상적으로 연결되었을 때:
    1. 로깅
    2. 통화 시작 시간 기록
    3. TTS로 인사말 재생 (향후 구현)
    """
    try:
        direct_call = payload.get("direct_call", {})
        call_id = direct_call.get("call_id")
        caller_id = direct_call.get("caller_id")
        callee_id = direct_call.get("callee_id")

        logger.info(f"✅ [CALL-ESTABLISHED] Call connected!")
        logger.info(f"   Call ID: {call_id}")
        logger.info(f"   Caller: {caller_id}")
        logger.info(f"   Callee: {callee_id}")

        # TODO: 향후 구현
        # 1. TTS로 AI 인사말 재생
        # 2. STT 활성화하여 사용자 음성 인식 시작
        # 3. 실시간 대화 처리

    except Exception as e:
        logger.error(f"❌ Call established handling error: {str(e)}")
        logger.error(f"   Payload: {payload}")


