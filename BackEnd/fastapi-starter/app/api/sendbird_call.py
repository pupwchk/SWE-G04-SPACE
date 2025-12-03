"""
SendBird Calls API
AI와 사용자 간 음성 통화 관리
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.services.sendbird_client import SendbirdCallsClient
from app.config.sendbird import SendbirdConfig
from app.utils.user_utils import get_user_by_identifier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calls", tags=["SendBird Calls"])


class InitiateCallRequest(BaseModel):
    """통화 시작 요청"""
    user_id: str = Field(..., description="사용자 ID (이메일 또는 UUID)")
    call_type: str = Field("voice", description="통화 타입 (voice/video)")


class InitiateCallResponse(BaseModel):
    """통화 시작 응답"""
    call_id: str
    caller_id: str
    callee_id: str
    call_type: str
    status: str


@router.post("/initiate", response_model=InitiateCallResponse)
async def initiate_call_to_ai(
    request: InitiateCallRequest,
    db: Session = Depends(get_db)
):
    """
    사용자가 AI assistant에게 전화 걸기 (서버에서 통화 생성)

    플로우:
    1. 사용자 존재 확인
    2. SendBird Calls Direct Call API로 통화 생성
    3. iOS 앱으로 통화 정보 반환
    4. iOS 앱이 통화 화면 표시

    Args:
        request: 통화 요청 정보

    Returns:
        통화 정보 (call_id 포함)
    """
    try:
        # 1. DB에서 사용자 확인
        user = get_user_by_identifier(db, request.user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User not found: {request.user_id}"
            )

        logger.info(f"📞 Initiating call: {request.user_id} -> {SendbirdConfig.AI_USER_ID}")

        # 2. SendBird Direct Call API로 통화 생성
        calls_client = SendbirdCallsClient()

        # Direct Call API 사용 (서버-투-서버)
        result = await calls_client.create_direct_call(
            caller_id=request.user_id,
            callee_id=SendbirdConfig.AI_USER_ID,
            call_type=request.call_type
        )

        logger.info(f"✅ Call created: {result.get('call_id')}")

        return InitiateCallResponse(
            call_id=result["call_id"],
            caller_id=result["caller"]["user_id"],
            callee_id=result["callee"]["user_id"],
            call_type=result.get("call_type", request.call_type),
            status=result.get("status", "ringing")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to initiate call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-call/{user_id}")
async def ai_call_user(
    user_id: str,
    call_type: str = "voice",
    db: Session = Depends(get_db)
):
    """
    AI assistant가 사용자에게 전화 걸기

    사용 예시:
    - 긴급 상황 감지 시
    - 사용자 건강 이상 감지 시
    - 중요한 알림이 있을 때

    Args:
        user_id: 사용자 ID (이메일 또는 UUID)
        call_type: 통화 타입 (voice/video)

    Returns:
        통화 정보
    """
    try:
        # 사용자 확인
        user = get_user_by_identifier(db, user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User not found: {user_id}"
            )

        logger.info(f"📞 AI calling user: {SendbirdConfig.AI_USER_ID} -> {user_id}")

        # Direct Call API 사용
        calls_client = SendbirdCallsClient()
        result = await calls_client.create_direct_call(
            caller_id=SendbirdConfig.AI_USER_ID,
            callee_id=user_id,
            call_type=call_type
        )

        logger.info(f"✅ AI call created: {result.get('call_id')}")

        return {
            "call_id": result["call_id"],
            "caller_id": result["caller"]["user_id"],
            "callee_id": result["callee"]["user_id"],
            "call_type": result.get("call_type", call_type),
            "status": result.get("status", "ringing")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ AI call failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{call_id}")
async def get_call_status(call_id: str):
    """
    통화 상태 조회

    Args:
        call_id: 통화 ID

    Returns:
        통화 상태 정보
    """
    try:
        calls_client = SendbirdCallsClient()
        result = await calls_client.get_call_info(call_id)

        return result

    except Exception as e:
        logger.error(f"❌ Failed to get call status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
