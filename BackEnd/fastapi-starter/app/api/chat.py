# app/api/chat.py
"""
시나리오 2: 사용자 주도형 대화 API
사용자가 불편함을 표현하면 AI가 가전 제어를 제안하고, 사용자 승인 후 실행
"""
import os
import logging
from uuid import UUID
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.config.db import get_db
from app.services.llm_service import llm_service
from app.services.appliance_control_service import appliance_control_service
from app.services.appliance_rule_engine import appliance_rule_engine
from app.services.weather_service import weather_service
from app.services.hrv_service import hrv_service
from app.services.supabase_service import supabase_persona_service
from app.models.user import User
from app.models.location import UserLocation
from app.models.appliance import UserAppliancePreference
from app.cruds import chat as chat_cruds
from app.utils.user_utils import get_user_uuid_by_identifier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


# ========== 스키마 정의 ==========

class ChatMessageRequest(BaseModel):
    """채팅 메시지 요청"""
    message: str = Field(..., description="사용자 메시지")
    context: Optional[Dict[str, Any]] = Field(None, description="추가 컨텍스트")
    character_id: Optional[str] = Field(None, description="페르소나 character ID")


class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답"""
    user_message: str
    ai_response: str
    intent_type: str
    needs_control: bool
    suggestions: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None


class ApplianceApprovalRequest(BaseModel):
    """가전 제어 승인 요청"""
    user_response: str = Field(..., description="사용자 응답 (예: '좋아', '에어컨은 24도로')")
    original_plan: Dict[str, Any] = Field(..., description="원래 제안된 제어 계획")
    session_id: Optional[str] = Field(None, description="세션 ID")


class ApplianceApprovalResponse(BaseModel):
    """가전 제어 승인 응답"""
    approved: bool
    has_modification: bool
    modifications: Optional[Dict[str, Any]] = None
    execution_results: Optional[List[Dict[str, Any]]] = None
    ai_response: str


# ========== 메모리 관리 (임시) ==========
# TODO: DB로 이관 필요
from collections import OrderedDict
from datetime import datetime, timedelta

# 최대 세션 수와 타임아웃 설정
MAX_SESSIONS = 100
SESSION_TIMEOUT = timedelta(hours=2)
MAX_HISTORY_PER_SESSION = 50

chat_sessions: OrderedDict[str, Dict[str, Any]] = OrderedDict()


def cleanup_old_sessions():
    """오래된 세션 정리"""
    now = datetime.now()
    to_delete = []

    for session_id, session in chat_sessions.items():
        last_accessed = session.get("last_accessed", now)
        if now - last_accessed > SESSION_TIMEOUT:
            to_delete.append(session_id)

    for session_id in to_delete:
        del chat_sessions[session_id]
        logger.info(f"🗑️ Cleaned up old session: {session_id}")

    # 최대 개수 초과 시 오래된 것부터 삭제 (LRU)
    while len(chat_sessions) > MAX_SESSIONS:
        oldest_session_id = next(iter(chat_sessions))
        del chat_sessions[oldest_session_id]
        logger.info(f"🗑️ Evicted session (max limit): {oldest_session_id}")


def get_or_create_session(user_id: str) -> str:
    """세션 ID 생성 또는 조회"""
    session_id = f"session_{user_id}"

    # 주기적 정리 (10% 확률로 실행)
    import random
    if random.random() < 0.1:
        cleanup_old_sessions()

    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "user_id": user_id,
            "conversation_history": [],
            "pending_suggestions": None,
            "dialogue_state": {  # DST: 대화 상태 추적
                "intent": None,
                "slots": {},  # 현재 제어 중인 가전 정보 {"appliance": "에어컨", "temperature": 24}
                "appliance_states": {}  # 가전 현재 상태 캐시
            },
            "last_accessed": datetime.now()
        }
    else:
        # 세션 접근 시간 갱신 (LRU)
        chat_sessions[session_id]["last_accessed"] = datetime.now()
        # OrderedDict에서 최신 항목으로 이동
        chat_sessions.move_to_end(session_id)

    return session_id


# ========== API 엔드포인트 ==========

@router.post("/{user_identifier}/message", response_model=ChatMessageResponse)
async def send_chat_message(
    user_identifier: str,
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    시나리오 2 - 사용자 메시지 처리 (1단계)
    user_identifier: 사용자 email 또는 UUID

    플로우:
    1. 사용자 메시지 수신 ("덥다", "건조하다" 등)
    2. LLM이 의도 파싱 (environment_complaint, appliance_request, general_chat)
    3. environment_complaint인 경우:
       - 현재 상태 조회 (날씨, 피로도, 가전 상태)
       - 가전 제어 추천 생성
       - 자연어 제안 메시지 생성
       - 제안 내용 세션에 저장
    4. 응답 반환

    예시:
    Request:
        {"message": "집이 너무 덥다"}

    Response:
        {
            "user_message": "집이 너무 덥다",
            "ai_response": "현재 온도가 28도로 높고, 피로도가 3이에요. 에어컨을 23도로 켜고, 공기청정기도 켤까요?",
            "intent_type": "environment_complaint",
            "needs_control": true,
            "suggestions": [
                {"appliance_type": "에어컨", "action": "on", "settings": {"target_temp_c": 23}},
                {"appliance_type": "공기청정기", "action": "on"}
            ],
            "session_id": "session_user123"
        }
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)
        user_id = str(user_uuid)

        # 메모리 세션 (빠른 응답용)
        session_id = get_or_create_session(user_identifier)
        session = chat_sessions[session_id]

        # DB 세션 (영구 저장용)
        db_session = chat_cruds.get_or_create_session(
            db=db,
            user_id=user_uuid,
            persona_id=request.character_id,
            persona_nickname=None  # 나중에 업데이트
        )

        # 페르소나 로드 (character_id가 있으면)
        persona = None
        if request.character_id:
            # 1순위: Supabase 페르소나 시스템 시도
            if supabase_persona_service.is_available():
                persona = supabase_persona_service.get_persona_for_llm(request.character_id)
                if persona:
                    logger.info(f"✅ Loaded Supabase persona: {persona['nickname']}")
                else:
                    logger.warning(f"⚠️ Supabase persona not found: {request.character_id}, falling back to FastAPI Character")

            # 2순위: FastAPI Character 테이블 (fallback)
            if not persona:
                from app.cruds import info as infoCruds
                character = infoCruds.get_character(db, UUID(request.character_id))
                if character:
                    persona = {
                        "nickname": character.nickname,
                        "description": character.persona
                    }
                    logger.info(f"✅ Loaded FastAPI persona: {character.nickname}")
                else:
                    logger.warning(f"⚠️ Character not found in both Supabase and FastAPI DB: {request.character_id}")

        # 1. 의도 파싱
        intent_result = await llm_service.parse_user_intent(
            user_message=request.message,
            context=request.context
        )

        logger.info(f"📝 Intent: {intent_result}")

        # 대화 히스토리 저장 (메모리 - 최대 개수 제한)
        session["conversation_history"].append({
            "role": "user",
            "message": request.message,
            "intent": intent_result
        })
        # 히스토리 제한
        if len(session["conversation_history"]) > MAX_HISTORY_PER_SESSION:
            session["conversation_history"] = session["conversation_history"][-MAX_HISTORY_PER_SESSION:]

        intent_type = intent_result.get("intent_type")
        needs_control = intent_result.get("needs_control", False)

        # ✅ DB에 사용자 메시지 저장
        chat_cruds.save_message(
            db=db,
            session_id=db_session.id,
            role="user",
            content=request.message,
            intent_type=intent_type,
            needs_control=needs_control
        )

        # LLM이 잘못 판단할 수 있으므로, environment_complaint나 appliance_request는 무조건 제어 필요
        if intent_type in ["environment_complaint", "appliance_request"]:
            needs_control = True

        # DST 상태 업데이트
        session["dialogue_state"]["intent"] = intent_type
        if intent_type == "appliance_request" and intent_result.get("issues"):
            # 가전 제어 요청인 경우 슬롯 추출
            for issue in intent_result["issues"]:
                session["dialogue_state"]["slots"][issue.get("type")] = issue.get("condition")

        # 현재 가전 상태 조회 (DST에 포함)
        appliance_states = appliance_control_service.get_appliance_status(
            db=db,
            user_id=user_id
        )
        session["dialogue_state"]["appliance_states"] = appliance_states

        # 2. 일반 대화인 경우
        if intent_type == "general_chat" or not needs_control:
            # 대화 히스토리를 OpenAI 포맷으로 변환
            history_for_llm = [
                {"role": msg["role"], "content": msg["message"]}
                for msg in session["conversation_history"][-10:]  # 최근 10개
            ]

            # 날씨 정보 조회 (일반 대화에도 컨텍스트 제공)
            user_location = db.query(UserLocation).filter(UserLocation.user_id == UUID(user_id)).first()
            home_lat = user_location.home_latitude if user_location and user_location.home_latitude else 37.5665
            home_lng = user_location.home_longitude if user_location and user_location.home_longitude else 126.9780

            # 위치가 0,0이면 서울 기본 위치 사용
            if home_lat == 0.0 or home_lng == 0.0:
                home_lat = 37.5665
                home_lng = 126.9780

            weather_data = await weather_service.get_combined_weather(
                db=db,
                latitude=home_lat,
                longitude=home_lng,
                sido_name=os.getenv("DEFAULT_SIDO_NAME", "서울")
            )

            # 피로도 정보도 제공
            fatigue_level = hrv_service.get_latest_fatigue_level(db, UUID(user_id))

            # 컨텍스트 구성
            context = {
                "weather": weather_data,
                "fatigue_level": fatigue_level,
                "location": {
                    "latitude": home_lat,
                    "longitude": home_lng
                }
            }

            llm_result = await llm_service.generate_response(
                user_message=request.message,
                conversation_history=history_for_llm,  # ← 대화 히스토리 전달
                persona=persona,
                context=context,  # ← 날씨 및 상태 정보 전달
                appliance_states=appliance_states,  # ← 현재 가전 상태 전달
                dialogue_state=session["dialogue_state"]  # ← DST 상태 전달
            )
            ai_response = llm_result.get("response", "죄송합니다. 응답을 생성할 수 없습니다.")

            # 메모리 저장
            session["conversation_history"].append({
                "role": "assistant",
                "message": ai_response
            })

            # ✅ DB에 AI 응답 저장
            chat_cruds.save_message(
                db=db,
                session_id=db_session.id,
                role="assistant",
                content=ai_response
            )

            return ChatMessageResponse(
                user_message=request.message,
                ai_response=ai_response,
                intent_type=intent_type,
                needs_control=False,
                session_id=session_id
            )

        # 3. 가전 제어가 필요한 경우
        # 3-1. 현재 상태 조회
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 사용자 위치 정보 조회
        user_location = db.query(UserLocation).filter(UserLocation.user_id == UUID(user_id)).first()
        home_lat = user_location.home_latitude if user_location and user_location.home_latitude else 37.5665
        home_lng = user_location.home_longitude if user_location and user_location.home_longitude else 126.9780

        # 위치가 0,0이면 서울 기본 위치 사용
        if home_lat == 0.0 or home_lng == 0.0:
            home_lat = 37.5665
            home_lng = 126.9780

        # 날씨 정보
        weather_data = await weather_service.get_combined_weather(
            db=db,
            latitude=home_lat,
            longitude=home_lng,
            sido_name=os.getenv("DEFAULT_SIDO_NAME", "서울")
        )

        # 피로도
        fatigue_level = hrv_service.get_latest_fatigue_level(db, UUID(user_id))
        if fatigue_level is None:
            fatigue_level = 2  # 기본값

        # 3-2. 사용자 메시지 기반 가전 제어 추천
        # Step 1: LLM이 사용자 메시지를 분석하여 어떤 가전이 필요한지 판단
        history_for_llm = [
            {"role": msg["role"], "content": msg["message"]}
            for msg in session["conversation_history"][-10:]
        ]

        suggestion_result = await llm_service.generate_user_request_suggestion(
            user_message=request.message,
            appliance_states=appliance_states,
            weather=weather_data,
            fatigue_level=fatigue_level,
            persona=persona,
            conversation_history=history_for_llm
        )

        llm_appliances = suggestion_result.get("appliances", [])

        # Step 2: LLM이 추천한 가전에 대해 선호 세팅 테이블에서 실제 설정값 조회
        recommendations = []
        for llm_app in llm_appliances:
            appliance_type = llm_app["appliance_type"]
            action = llm_app.get("action", "on")
            llm_settings = llm_app.get("settings", {})
            settings_source = "default"  # "preference" | "user_input" | "default"

            if action == "on":
                # 선호 세팅 테이블 조회
                preference = db.query(UserAppliancePreference).filter(
                    UserAppliancePreference.user_id == UUID(user_id),
                    UserAppliancePreference.fatigue_level == fatigue_level,
                    UserAppliancePreference.appliance_type == appliance_type
                ).first()

                # ✅ is_learned=True인 경우만 학습된 선호 세팅으로 취급
                if preference and preference.settings_json and preference.is_learned:
                    # 사용자가 실제로 승인/수정한 학습된 선호 세팅 사용
                    settings_json = preference.settings_json
                    settings_source = "preference"

                    # 에어컨의 경우 냉방/난방 모드 선택
                    if appliance_type == "에어컨" and isinstance(settings_json, dict):
                        # 현재 온도 기반으로 냉방/난방 판단
                        current_temp = weather_data.get('temperature', 20)
                        if current_temp >= 24:
                            # 더우면 냉방
                            mode_key = "cool"
                        else:
                            # 추우면 난방
                            mode_key = "heat"

                        # cool/heat 키가 있으면 선택, 없으면 전체 사용
                        if mode_key in settings_json:
                            settings = settings_json[mode_key]
                        elif "cool" in settings_json or "heat" in settings_json:
                            # cool만 있거나 heat만 있는 경우
                            settings = settings_json.get(mode_key) or settings_json.get("cool") or settings_json.get("heat")
                        else:
                            # 직접 설정값인 경우
                            settings = settings_json
                    else:
                        settings = settings_json

                    logger.info(f"📚 Using preference for {appliance_type}: {settings}")
                elif llm_settings:
                    # LLM이 제안한 설정 사용 (사용자가 구체적인 값을 말한 경우)
                    settings = llm_settings
                    settings_source = "user_input"
                    logger.info(f"🤖 Using LLM settings for {appliance_type}: {settings}")
                else:
                    # 기본값 사용
                    from app.services.appliance_control_service import appliance_control_service
                    settings = appliance_control_service._get_default_settings(appliance_type)
                    settings_source = "default"
                    logger.info(f"⚙️ Using default settings for {appliance_type}: {settings}")
            else:
                settings = {}

            recommendations.append({
                "appliance_type": appliance_type,
                "action": action,
                "settings": settings,
                "reason": llm_app.get("reason", ""),
                "settings_source": settings_source  # 설정값 출처 추가
            })

        if not recommendations:
            # 제어가 필요 없는 경우 - LLM 응답 사용
            ai_response = suggestion_result.get("response", "현재 집안 환경은 적절한 상태입니다. 다른 도움이 필요하신가요?")
            session["conversation_history"].append({
                "role": "assistant",
                "message": ai_response
            })

            # ✅ DB에 AI 응답 저장
            chat_cruds.save_message(
                db=db,
                session_id=db_session.id,
                role="assistant",
                content=ai_response
            )

            return ChatMessageResponse(
                user_message=request.message,
                ai_response=ai_response,
                intent_type=intent_type,
                needs_control=False,
                session_id=session_id
            )

        # Step 3: 실제 설정값을 포함한 자연어 제안 메시지 생성
        ai_response = await llm_service.generate_appliance_suggestion(
            appliances=recommendations,
            weather=weather_data,
            fatigue_level=fatigue_level,
            user_message=request.message,
            persona=persona,
            appliance_states=appliance_states,
            conversation_history=history_for_llm
        )

        # 3-4. 세션에 저장
        session["pending_suggestions"] = {
            "recommendations": recommendations,
            "weather": weather_data,
            "fatigue_level": fatigue_level,
            "intent_type": intent_type,  # ✅ intent_type 저장 (preference 학습 여부 판단용)
            "timestamp": None  # TODO: 타임스탬프 추가
        }

        # 메모리 저장
        session["conversation_history"].append({
            "role": "assistant",
            "message": ai_response,
            "suggestions": recommendations
        })

        # ✅ DB에 AI 응답 저장 (가전 제어 제안 포함)
        chat_cruds.save_message(
            db=db,
            session_id=db_session.id,
            role="assistant",
            content=ai_response,
            suggestions=recommendations
        )

        logger.info(f"✅ Suggestions generated: {len(recommendations)} appliances")

        return ChatMessageResponse(
            user_message=request.message,
            ai_response=ai_response,
            intent_type=intent_type,
            needs_control=True,
            suggestions=recommendations,
            session_id=session_id
        )

    except Exception as e:
        logger.error(f"❌ Chat message error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_identifier}/approve", response_model=ApplianceApprovalResponse)
async def approve_appliance_control(
    user_identifier: str,
    request: ApplianceApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    시나리오 2 - 가전 제어 승인 처리 (2단계)
    user_identifier: 사용자 email 또는 UUID

    플로우:
    1. 사용자 승인/거절/수정 응답 수신
    2. LLM이 응답 파싱 (approved, has_modification, modifications)
    3. approved=true인 경우:
       - 수정 사항 적용
       - 가전 제어 실행
       - 실행 결과 반환
    4. approved=false인 경우:
       - 거절 메시지 반환

    예시 1 (승인):
    Request:
        {
            "user_response": "좋아",
            "original_plan": {"recommendations": [...]}
        }

    Response:
        {
            "approved": true,
            "has_modification": false,
            "execution_results": [
                {"appliance": "에어컨", "status": "success"},
                {"appliance": "공기청정기", "status": "success"}
            ],
            "ai_response": "에어컨을 23도로 켜고 공기청정기를 켰습니다."
        }

    예시 2 (수정 후 승인):
    Request:
        {
            "user_response": "에어컨은 24도로 해줘",
            "original_plan": {"recommendations": [...]}
        }

    Response:
        {
            "approved": true,
            "has_modification": true,
            "modifications": {"에어컨": {"target_temp_c": 24}},
            "execution_results": [
                {"appliance": "에어컨", "status": "success"},
                {"appliance": "공기청정기", "status": "success"}
            ],
            "ai_response": "에어컨을 24도로 수정해서 켜고 공기청정기를 켰습니다."
        }

    예시 3 (거절):
    Request:
        {
            "user_response": "아니야, 괜찮아",
            "original_plan": {"recommendations": [...]}
        }

    Response:
        {
            "approved": false,
            "has_modification": false,
            "ai_response": "알겠습니다. 필요하시면 언제든 말씀해주세요."
        }
    """
    try:
        # user_identifier를 UUID로 변환
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)
        user_id = str(user_uuid)

        session_id = get_or_create_session(user_identifier)
        session = chat_sessions[session_id]

        # 1. 승인/거절/수정 파싱
        approval_result = await llm_service.detect_modification(
            original_plan=request.original_plan,
            user_response=request.user_response
        )

        logger.info(f"📝 Approval: {approval_result}")

        # 2. 거절인 경우 (시나리오 2)
        if not approval_result.get("approved", False):
            # ✅ environment_complaint인 경우만 조건 임계값 수정
            # appliance_request (직접 명령)는 조건 테이블 수정 안함
            from app.models.appliance import ApplianceConditionRule

            pending = session.get("pending_suggestions")
            original_intent = pending.get("intent_type") if pending else None

            if pending and pending.get("recommendations") and original_intent == "environment_complaint":
                # "덥다", "건조하다" 등 환경 불편 표현 → 조건 기반 추천 → 기각 시 조건 수정 ✅
                fatigue_level = pending.get("fatigue_level")
                weather_data = pending.get("weather", {})

                # 현재 날씨 정보
                current_temp = weather_data.get("temperature")
                current_humidity = weather_data.get("humidity")
                current_pm10 = weather_data.get("pm10")

                for rec in pending["recommendations"]:
                    appliance_type = rec.get("appliance_type")

                    # 해당 가전의 조건 규칙 조회 및 임계값 수정
                    try:
                        rules = db.query(ApplianceConditionRule).filter(
                            ApplianceConditionRule.user_id == user_uuid,
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
                                    # "더울 때 켜기" 규칙 → 임계값 상향 (더 더워야 켜짐)
                                    new_threshold = max(current_temp + margin, old_threshold + margin)
                                    condition["temp_threshold"] = new_threshold
                                    updated = True
                                    logger.info(f"📈 Updated temp threshold (>=): {old_threshold}°C → {new_threshold}°C for {appliance_type}")
                                elif condition.get("operator") == "<=":
                                    # "추울 때 켜기" 규칙 → 임계값 하향 (더 추워야 켜짐)
                                    new_threshold = min(current_temp - margin, old_threshold - margin)
                                    condition["temp_threshold"] = new_threshold
                                    updated = True
                                    logger.info(f"📉 Updated temp threshold (<=): {old_threshold}°C → {new_threshold}°C for {appliance_type}")

                            # 습도 기반 조건 수정
                            if "humidity_threshold" in condition and current_humidity is not None:
                                old_threshold = condition["humidity_threshold"]
                                margin = 5  # 5% 마진

                                if condition.get("operator") == ">=":
                                    # "습할 때 켜기" (제습기) → 임계값 상향
                                    new_threshold = max(current_humidity + margin, old_threshold + margin)
                                    condition["humidity_threshold"] = new_threshold
                                    updated = True
                                    logger.info(f"📈 Updated humidity threshold (>=): {old_threshold}% → {new_threshold}% for {appliance_type}")
                                elif condition.get("operator") == "<=":
                                    # "건조할 때 켜기" (가습기) → 임계값 하향
                                    new_threshold = min(current_humidity - margin, old_threshold - margin)
                                    condition["humidity_threshold"] = new_threshold
                                    updated = True
                                    logger.info(f"📉 Updated humidity threshold (<=): {old_threshold}% → {new_threshold}% for {appliance_type}")

                            # 미세먼지 기반 조건 수정
                            if "pm10_threshold" in condition and current_pm10 is not None:
                                old_threshold = condition["pm10_threshold"]
                                margin = 10  # 10㎍/㎥ 마진

                                if condition.get("operator") == ">=":
                                    # "미세먼지 나쁠 때 켜기" → 임계값 상향
                                    new_threshold = max(current_pm10 + margin, old_threshold + margin)
                                    condition["pm10_threshold"] = new_threshold
                                    updated = True
                                    logger.info(f"📈 Updated pm10 threshold: {old_threshold} → {new_threshold} for {appliance_type}")

                            if updated:
                                rule.condition_json = condition

                        db.commit()
                        logger.info(f"✅ Updated condition thresholds for {appliance_type} (rejected in scenario2, intent=environment_complaint)")
                    except Exception as e:
                        logger.error(f"⚠️ Failed to update condition for {appliance_type}: {str(e)}")
                        db.rollback()
            elif original_intent == "appliance_request":
                # "에어컨 켜줘" 등 직접 명령 → 기각해도 조건 테이블 수정 안함
                logger.info(f"⏭️ Skipping condition update on rejection [appliance_request - user direct command]")

            ai_response = "알겠습니다. 필요하시면 언제든 말씀해주세요."
            session["conversation_history"].append({
                "role": "user",
                "message": request.user_response
            })
            session["conversation_history"].append({
                "role": "assistant",
                "message": ai_response
            })
            session["pending_suggestions"] = None

            # DST 상태 초기화 (거절)
            session["dialogue_state"]["intent"] = None
            session["dialogue_state"]["slots"] = {}

            return ApplianceApprovalResponse(
                approved=False,
                has_modification=False,
                ai_response=ai_response
            )

        # 3. 승인인 경우 - 가전 제어 실행
        recommendations = request.original_plan.get("recommendations", [])
        modifications = approval_result.get("modifications", {})
        has_modification = approval_result.get("has_modification", False)

        # 현재 피로도 조회 (선호 세팅 저장용)
        fatigue_level = hrv_service.get_latest_fatigue_level(db, user_uuid)
        if fatigue_level is None:
            fatigue_level = 2  # 기본값

        # 한글 모드명을 영문으로 변환하는 매핑
        MODE_TRANSLATION = {
            "냉방": "cool",
            "난방": "heat",
            "송풍": "fan",
            "제습": "dry",
            "자동": "auto"
        }

        execution_results = []

        for rec in recommendations:
            appliance_type = rec["appliance_type"]
            action = rec["action"]
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
                        try:
                            preference = db.query(UserAppliancePreference).filter(
                                UserAppliancePreference.user_id == user_uuid,
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

                logger.info(f"🔧 Modified {appliance_type}: {settings}")

            # 가전 제어 실행
            try:
                result = appliance_control_service.execute_command(
                    db=db,
                    user_id=user_id,
                    appliance_type=appliance_type,
                    action=action,
                    settings=settings,
                    triggered_by="chat_scenario2"
                )

                execution_results.append({
                    "appliance": appliance_type,
                    "action": action,
                    "settings": settings,
                    "status": "success",
                    "result": result
                })
                logger.info(f"✅ {appliance_type} {action} success")

                # ✨ 선호 세팅 학습: environment_complaint인 경우만 학습
                # appliance_request (직접 명령)는 학습하지 않음
                pending = session.get("pending_suggestions")
                original_intent = pending.get("intent_type") if pending else None

                if action == "on" and settings and original_intent == "environment_complaint":
                    # "덥다", "건조하다" 등 환경 불편 표현 → 조건 기반 추천 → 학습 ✅
                    try:
                        preference = db.query(UserAppliancePreference).filter(
                            UserAppliancePreference.user_id == user_uuid,
                            UserAppliancePreference.fatigue_level == fatigue_level,
                            UserAppliancePreference.appliance_type == appliance_type
                        ).first()

                        if preference:
                            # 기존 선호 세팅 업데이트
                            preference.settings_json = settings
                            preference.is_learned = True  # ✅ 사용자가 승인했으므로 학습됨으로 표시
                            logger.info(f"📝 Updated preference (is_learned=True) for {appliance_type} at fatigue {fatigue_level} [environment_complaint]")
                        else:
                            # 새로운 선호 세팅 생성
                            new_preference = UserAppliancePreference(
                                user_id=user_uuid,
                                fatigue_level=fatigue_level,
                                appliance_type=appliance_type,
                                settings_json=settings,
                                is_learned=True  # ✅ 사용자가 승인했으므로 학습됨으로 표시
                            )
                            db.add(new_preference)
                            logger.info(f"✨ Created new preference (is_learned=True) for {appliance_type} at fatigue {fatigue_level} [environment_complaint]")

                        db.commit()
                    except Exception as pref_error:
                        logger.error(f"⚠️ Failed to save preference: {str(pref_error)}")
                        db.rollback()
                elif original_intent == "appliance_request":
                    # "에어컨 켜줘" 등 직접 명령 → 학습하지 않음 ❌
                    logger.info(f"⏭️ Skipping preference learning for {appliance_type} [appliance_request - user direct command]")

            except Exception as e:
                execution_results.append({
                    "appliance": appliance_type,
                    "action": action,
                    "status": "error",
                    "error": str(e)
                })
                logger.error(f"❌ {appliance_type} {action} error: {str(e)}")

        # 4. 응답 메시지 생성 - LLM을 사용해서 자연스럽게
        success_count = sum(1 for r in execution_results if r["status"] == "success")
        total_count = len(execution_results)

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
                # 페르소나 정보 조회 (session에서)
                persona = None
                db_session = chat_cruds.get_or_create_session(
                    db=db,
                    user_id=user_uuid,
                    persona_id=None,
                    persona_nickname=None
                )
                if db_session.persona_id:
                    # Supabase 페르소나 시스템 시도
                    if supabase_persona_service.is_available():
                        persona = supabase_persona_service.get_persona_for_llm(db_session.persona_id)

                ai_response = await llm_service.generate_appliance_execution_result(
                    appliances=success_appliances,
                    has_modification=has_modification,
                    persona=persona
                )
            except Exception as llm_error:
                logger.warning(f"⚠️ LLM response generation failed, using fallback: {llm_error}")
                # Fallback
                if has_modification:
                    ai_response = "수정하신 내용으로 제어했어요!"
                else:
                    ai_response = "알겠습니다. 제어했어요!"
        else:
            # 전부 실패한 경우
            ai_response = f"가전 제어에 실패했습니다. ({success_count}/{total_count}개 성공)"

        # 세션 업데이트
        session["conversation_history"].append({
            "role": "user",
            "message": request.user_response
        })
        session["conversation_history"].append({
            "role": "assistant",
            "message": ai_response,
            "execution_results": execution_results
        })
        session["pending_suggestions"] = None

        # DST 상태 초기화 (가전 제어 완료)
        session["dialogue_state"]["intent"] = None
        session["dialogue_state"]["slots"] = {}

        # 가전 상태 갱신
        updated_appliance_states = appliance_control_service.get_appliance_status(
            db=db,
            user_id=user_id
        )
        session["dialogue_state"]["appliance_states"] = updated_appliance_states

        return ApplianceApprovalResponse(
            approved=True,
            has_modification=has_modification,
            modifications=modifications if has_modification else None,
            execution_results=execution_results,
            ai_response=ai_response
        )

    except Exception as e:
        logger.error(f"❌ Approval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_identifier}/history")
async def get_chat_history(
    user_identifier: str,
    limit: int = 20,
    persona_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    채팅 히스토리 조회
    user_identifier: 사용자 email 또는 UUID (서버 DB UUID 또는 Supabase UUID)
    persona_id: 페르소나 ID (선택적, 향후 페르소나별 히스토리 필터링 지원 가능)

    Returns:
        {
            "user_id": "user123",
            "session_id": "session_user123",
            "conversation_history": [
                {"role": "user", "message": "덥다", "intent": {...}},
                {"role": "assistant", "message": "에어컨을 켤까요?", "suggestions": [...]}
            ]
        }
    """
    try:
        # user_identifier 검증 (Supabase UUID → 이메일 → 서버 DB UUID 변환 포함)
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        # 세션 ID는 이메일 기반으로 생성 (일관성 유지)
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 이메일을 기준으로 세션 ID 생성 (메모리 세션은 이메일 기반)
        session_id = get_or_create_session(user.email)
        session = chat_sessions[session_id]

        history = session["conversation_history"][-limit:]

        return {
            "user_id": str(user_uuid),
            "email": user.email,
            "session_id": session_id,
            "conversation_history": history,
            "has_pending_suggestions": session["pending_suggestions"] is not None,
            "persona_id": persona_id  # 요청된 페르소나 ID 반환 (향후 활용)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ History error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_identifier}/session")
async def clear_chat_session(
    user_identifier: str,
    db: Session = Depends(get_db)
):
    """
    채팅 세션 초기화
    user_identifier: 사용자 email 또는 UUID

    Returns:
        {"status": "ok", "message": "Session cleared"}
    """
    try:
        # user_identifier 검증
        user_uuid = get_user_uuid_by_identifier(db, user_identifier)

        session_id = f"session_{user_identifier}"
        if session_id in chat_sessions:
            del chat_sessions[session_id]
            logger.info(f"🗑️ Session cleared: {session_id}")

        return {
            "status": "ok",
            "message": "Session cleared"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Clear session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
