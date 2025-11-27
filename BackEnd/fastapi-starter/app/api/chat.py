# app/api/chat.py
"""
시나리오 2: 사용자 주도형 대화 API
사용자가 불편함을 표현하면 AI가 가전 제어를 제안하고, 사용자 승인 후 실행
"""
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
from app.models.user import User
from app.models.location import UserLocation
from app.models.appliance import UserAppliancePreference

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


# ========== 스키마 정의 ==========

class ChatMessageRequest(BaseModel):
    """채팅 메시지 요청"""
    message: str = Field(..., description="사용자 메시지")
    context: Optional[Dict[str, Any]] = Field(None, description="추가 컨텍스트")


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
chat_sessions: Dict[str, Dict[str, Any]] = {}


def get_or_create_session(user_id: str) -> str:
    """세션 ID 생성 또는 조회"""
    session_id = f"session_{user_id}"
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "user_id": user_id,
            "conversation_history": [],
            "pending_suggestions": None
        }
    return session_id


# ========== API 엔드포인트 ==========

@router.post("/{user_id}/message", response_model=ChatMessageResponse)
async def send_chat_message(
    user_id: str,
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    시나리오 2 - 사용자 메시지 처리 (1단계)

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
        session_id = get_or_create_session(user_id)
        session = chat_sessions[session_id]

        # 1. 의도 파싱
        intent_result = await llm_service.parse_user_intent(
            user_message=request.message,
            context=request.context
        )

        logger.info(f"📝 Intent: {intent_result}")

        # 대화 히스토리 저장
        session["conversation_history"].append({
            "role": "user",
            "message": request.message,
            "intent": intent_result
        })

        intent_type = intent_result.get("intent_type")
        needs_control = intent_result.get("needs_control", False)

        # LLM이 잘못 판단할 수 있으므로, environment_complaint나 appliance_request는 무조건 제어 필요
        if intent_type in ["environment_complaint", "appliance_request"]:
            needs_control = True

        # 2. 일반 대화인 경우
        if intent_type == "general_chat" or not needs_control:
            llm_result = await llm_service.generate_response(request.message)
            ai_response = llm_result.get("response", "죄송합니다. 응답을 생성할 수 없습니다.")
            session["conversation_history"].append({
                "role": "assistant",
                "message": ai_response
            })

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
        home_lat = user_location.home_latitude if user_location else 37.5665
        home_lng = user_location.home_longitude if user_location else 126.9780

        # 날씨 정보
        weather_data = await weather_service.get_combined_weather(
            db=db,
            latitude=home_lat,
            longitude=home_lng,
            sido_name="서울"
        )

        # 피로도
        fatigue_level = hrv_service.get_latest_fatigue_level(db, UUID(user_id))

        # 3-2. 가전 제어 추천 생성
        recommendations = appliance_rule_engine.get_appliances_to_control(
            db=db,
            user_id=user_id,
            weather_data=weather_data
        )

        if not recommendations:
            # 제어가 필요 없는 경우
            ai_response = "현재 집안 환경은 적절한 상태입니다. 다른 도움이 필요하신가요?"
            session["conversation_history"].append({
                "role": "assistant",
                "message": ai_response
            })

            return ChatMessageResponse(
                user_message=request.message,
                ai_response=ai_response,
                intent_type=intent_type,
                needs_control=False,
                session_id=session_id
            )

        # 3-3. 자연어 제안 생성
        ai_response = await llm_service.generate_appliance_suggestion(
            appliances=recommendations,
            weather=weather_data,
            fatigue_level=fatigue_level,
            user_message=request.message
        )

        # 3-4. 세션에 저장
        session["pending_suggestions"] = {
            "recommendations": recommendations,
            "weather": weather_data,
            "fatigue_level": fatigue_level,
            "timestamp": None  # TODO: 타임스탬프 추가
        }

        session["conversation_history"].append({
            "role": "assistant",
            "message": ai_response,
            "suggestions": recommendations
        })

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


@router.post("/{user_id}/approve", response_model=ApplianceApprovalResponse)
async def approve_appliance_control(
    user_id: str,
    request: ApplianceApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    시나리오 2 - 가전 제어 승인 처리 (2단계)

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
        session_id = get_or_create_session(user_id)
        session = chat_sessions[session_id]

        # 1. 승인/거절/수정 파싱
        approval_result = await llm_service.detect_modification(
            original_plan=request.original_plan,
            user_response=request.user_response
        )

        logger.info(f"📝 Approval: {approval_result}")

        # 2. 거절인 경우
        if not approval_result.get("approved", False):
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
        fatigue_level = hrv_service.get_latest_fatigue_level(db, UUID(user_id))
        if fatigue_level is None:
            fatigue_level = 2  # 기본값

        execution_results = []

        for rec in recommendations:
            appliance_type = rec["appliance_type"]
            action = rec["action"]
            settings = rec.get("settings", {})

            # 수정 사항 적용
            if has_modification and appliance_type in modifications:
                settings.update(modifications[appliance_type])
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

                # ✨ 선호 세팅 학습: UserAppliancePreference에 저장
                try:
                    preference = db.query(UserAppliancePreference).filter(
                        UserAppliancePreference.user_id == UUID(user_id),
                        UserAppliancePreference.fatigue_level == fatigue_level,
                        UserAppliancePreference.appliance_type == appliance_type
                    ).first()

                    if preference:
                        # 기존 선호 세팅 업데이트
                        preference.settings_json = settings
                        logger.info(f"📝 Updated preference for {appliance_type} at fatigue {fatigue_level}")
                    else:
                        # 새로운 선호 세팅 생성
                        new_preference = UserAppliancePreference(
                            user_id=UUID(user_id),
                            fatigue_level=fatigue_level,
                            appliance_type=appliance_type,
                            settings_json=settings
                        )
                        db.add(new_preference)
                        logger.info(f"✨ Created new preference for {appliance_type} at fatigue {fatigue_level}")

                    db.commit()
                except Exception as pref_error:
                    logger.error(f"⚠️ Failed to save preference: {str(pref_error)}")
                    db.rollback()

            except Exception as e:
                execution_results.append({
                    "appliance": appliance_type,
                    "action": action,
                    "status": "error",
                    "error": str(e)
                })
                logger.error(f"❌ {appliance_type} {action} error: {str(e)}")

        # 4. 응답 메시지 생성
        success_count = sum(1 for r in execution_results if r["status"] == "success")
        total_count = len(execution_results)

        if success_count == total_count:
            if has_modification:
                ai_response = f"수정하신 내용으로 {success_count}개 가전을 제어했습니다."
            else:
                ai_response = f"{success_count}개 가전을 제어했습니다."
        else:
            ai_response = f"{success_count}/{total_count}개 가전 제어에 성공했습니다."

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


@router.get("/{user_id}/history")
async def get_chat_history(
    user_id: str,
    limit: int = 20
):
    """
    채팅 히스토리 조회

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
        session_id = get_or_create_session(user_id)
        session = chat_sessions[session_id]

        history = session["conversation_history"][-limit:]

        return {
            "user_id": user_id,
            "session_id": session_id,
            "conversation_history": history,
            "has_pending_suggestions": session["pending_suggestions"] is not None
        }

    except Exception as e:
        logger.error(f"❌ History error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}/session")
async def clear_chat_session(user_id: str):
    """
    채팅 세션 초기화

    Returns:
        {"status": "ok", "message": "Session cleared"}
    """
    try:
        session_id = f"session_{user_id}"
        if session_id in chat_sessions:
            del chat_sessions[session_id]
            logger.info(f"🗑️ Session cleared: {session_id}")

        return {
            "status": "ok",
            "message": "Session cleared"
        }

    except Exception as e:
        logger.error(f"❌ Clear session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
