"""
SendBird 인증 API
iOS 앱에서 SendBird Calls SDK 초기화를 위한 인증 토큰 발급
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from app.config.db import get_db
from app.services.sendbird_client import SendbirdCallsClient
from app.utils.user_utils import get_user_by_identifier

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sendbird", tags=["SendBird Auth"])


class SendbirdAuthRequest(BaseModel):
    """SendBird 인증 요청"""
    user_id: str = Field(..., description="사용자 ID (이메일 또는 UUID)")
    nickname: Optional[str] = Field(None, description="사용자 닉네임")
    profile_url: Optional[str] = Field(None, description="프로필 이미지 URL")


class SendbirdAuthResponse(BaseModel):
    """SendBird 인증 응답"""
    user_id: str
    access_token: str
    calls_authenticated: bool
    error: Optional[str] = None


@router.post("/auth/token", response_model=SendbirdAuthResponse)
async def get_sendbird_auth_token(
    request: SendbirdAuthRequest,
    db: Session = Depends(get_db)
):
    """
    SendBird Calls 사용자 인증 토큰 발급

    iOS 앱에서 로그인 후 호출하여 SendBird Calls SDK 초기화용 access_token 획득

    플로우:
    1. 사용자 존재 여부 확인 (DB)
    2. SendBird Chat API로 사용자 생성/조회 및 access_token 발급
    3. SendBird Calls API로 인증
    4. iOS 앱으로 access_token 반환

    사용 예시 (iOS):
    ```swift
    // 1. 백엔드에서 토큰 발급
    let response = await apiClient.getSendbirdToken(userId: userEmail)

    // 2. SendBird Calls SDK 초기화
    SendBirdCall.authenticate(
        with: AuthenticateParams(userId: response.userId, accessToken: response.accessToken)
    ) { user, error in
        // 3. 통화 기능 사용 가능
    }
    ```

    Args:
        request: 사용자 인증 정보

    Returns:
        {
            "user_id": "user@example.com",
            "access_token": "abc123...",
            "calls_authenticated": true
        }
    """
    try:
        # 1. DB에서 사용자 확인
        user = get_user_by_identifier(db, request.user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User not found: {request.user_id}"
            )

        logger.info(f"🔐 Authenticating user '{request.user_id}' with SendBird Calls")

        # 2. SendBird Calls 클라이언트로 인증
        calls_client = SendbirdCallsClient()
        result = await calls_client.authenticate_user(
            user_id=request.user_id,
            nickname=request.nickname,
            profile_url=request.profile_url
        )

        # 3. 결과 반환
        if not result.get("access_token"):
            raise HTTPException(
                status_code=500,
                detail="Failed to obtain access_token from SendBird"
            )

        logger.info(f"✅ User '{request.user_id}' authenticated successfully")
        logger.info(f"   Calls authenticated: {result.get('calls_authenticated', False)}")

        return SendbirdAuthResponse(
            user_id=result["user_id"],
            access_token=result["access_token"],
            calls_authenticated=result.get("calls_authenticated", False),
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ SendBird auth error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/status/{user_id}")
async def check_sendbird_auth_status(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    SendBird 인증 상태 확인

    Args:
        user_id: 사용자 ID (이메일 또는 UUID)

    Returns:
        {
            "user_id": str,
            "exists": bool,
            "message": str
        }
    """
    try:
        # DB에서 사용자 확인
        user = get_user_by_identifier(db, user_id)
        if not user:
            return {
                "user_id": user_id,
                "exists": False,
                "message": "User not found in database"
            }

        # TODO: SendBird API로 실제 인증 상태 조회
        # 현재는 간단히 사용자 존재 여부만 반환
        return {
            "user_id": user_id,
            "exists": True,
            "message": "User exists in database. Call /auth/token to get SendBird token."
        }

    except Exception as e:
        logger.error(f"❌ Status check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auth/ai-token")
async def get_ai_assistant_token():
    """
    AI assistant의 access_token 발급

    무료 플랜에서는 iOS 앱이 AI assistant로도 인증해야 함.
    이 엔드포인트를 호출하여 AI assistant의 access_token을 받아서
    iOS 앱에서 SendBirdCall.authenticate() 호출.

    Returns:
        {
            "user_id": "home_ai_assistant",
            "access_token": str,
            "calls_ready": bool
        }
    """
    try:
        from app.config.sendbird import SendbirdConfig

        logger.info(f"🔑 Requesting AI assistant token for iOS app")

        # SendBird Calls 클라이언트로 AI assistant 등록 및 토큰 발급
        calls_client = SendbirdCallsClient()
        result = await calls_client.register_ai_assistant()

        if not result.get("access_token"):
            raise HTTPException(
                status_code=500,
                detail="Failed to obtain AI assistant access_token"
            )

        logger.info(f"✅ AI assistant token ready for iOS")

        return {
            "user_id": SendbirdConfig.AI_USER_ID,
            "access_token": result["access_token"],
            "calls_ready": result.get("calls_ready", True)
        }

    except Exception as e:
        logger.error(f"❌ AI token error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
