"""
사용자 관련 유틸리티 함수
Sendbird user_id(email)와 DB user_id(UUID) 매핑
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.models.user import User

logger = logging.getLogger(__name__)


def get_user_by_identifier(db: Session, user_identifier: str) -> Optional[User]:
    """
    사용자 식별자(email 또는 서버 DB UUID)로 User 조회

    우선순위:
    1. 서버 DB UUID로 조회
    2. Email로 조회
    3. Supabase UUID인 경우 → Supabase에서 이메일 조회 → Email로 조회

    Args:
        db: 데이터베이스 세션
        user_identifier: 사용자 식별자 (email 또는 UUID string)

    Returns:
        User 객체 또는 None
    """
    # 1. 서버 DB UUID로 시도
    try:
        user_uuid = UUID(user_identifier)
        user = db.query(User).filter(User.id == user_uuid).first()
        if user:
            return user
    except (ValueError, TypeError):
        # UUID 변환 실패 - email로 간주
        pass

    # 2. Email로 시도
    user = db.query(User).filter(User.email == user_identifier).first()
    if user:
        return user

    # 3. Supabase UUID인 경우 (서버 DB에 없지만 UUID 형식인 경우)
    # Supabase에서 이메일을 조회한 후, 그 이메일로 서버 DB 사용자 찾기
    try:
        # UUID 형식이지만 서버 DB에 없는 경우 → Supabase UUID일 가능성
        UUID(user_identifier)  # UUID 형식인지 확인

        from app.services.supabase_service import supabase_persona_service

        if supabase_persona_service.is_available():
            try:
                # Supabase에서 사용자 이메일 조회
                email = _get_email_from_supabase(user_identifier)
                if email:
                    logger.info(f"✅ [USER-MAPPING] Supabase UUID {user_identifier} mapped to email {email}")
                    user = db.query(User).filter(User.email == email).first()
                    if user:
                        return user
                    else:
                        logger.warning(f"⚠️ [USER-MAPPING] Email {email} found in Supabase but not in server DB")
            except Exception as e:
                logger.warning(f"⚠️ [USER-MAPPING] Failed to query Supabase for UUID {user_identifier}: {str(e)}")
    except (ValueError, TypeError):
        # UUID 형식도 아님
        pass

    return None


def _get_email_from_supabase(user_id: str) -> Optional[str]:
    """
    Supabase에서 user_id로 이메일 조회

    Args:
        user_id: Supabase user UUID

    Returns:
        이메일 또는 None
    """
    try:
        from app.services.supabase_service import supabase_persona_service

        if not supabase_persona_service.is_available():
            return None

        # Supabase Auth API를 통해 사용자 정보 조회
        client = supabase_persona_service.client

        # Supabase Admin API를 사용하여 사용자 정보 조회
        # auth.admin.get_user_by_id() 메서드 사용
        try:
            response = client.auth.admin.get_user_by_id(user_id)
            if response and response.user:
                email = response.user.email
                logger.info(f"✅ [SUPABASE-MAPPING] Found email {email} for Supabase UUID {user_id}")
                return email
        except AttributeError:
            # admin API가 없는 경우, 직접 DB 조회 시도
            result = client.table("users").select("email").eq("id", user_id).single().execute()
            if result.data:
                email = result.data.get("email")
                if email:
                    logger.info(f"✅ [SUPABASE-MAPPING] Found email {email} for Supabase UUID {user_id}")
                    return email

        logger.warning(f"⚠️ [SUPABASE-MAPPING] No email found for Supabase UUID {user_id}")
        return None

    except Exception as e:
        logger.error(f"❌ [SUPABASE-MAPPING] Error querying Supabase: {str(e)}")
        return None


def get_user_uuid_by_identifier(db: Session, user_identifier: str) -> UUID:
    """
    사용자 식별자(email 또는 UUID)로 UUID 조회

    Args:
        db: 데이터베이스 세션
        user_identifier: 사용자 식별자 (email 또는 UUID string)

    Returns:
        User의 UUID

    Raises:
        HTTPException: 사용자를 찾을 수 없는 경우
    """
    user = get_user_by_identifier(db, user_identifier)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_identifier}"
        )

    return user.id


def get_user_uuid_by_identifier_or_none(db: Session, user_identifier: str) -> Optional[UUID]:
    """
    사용자 식별자(email 또는 UUID)로 UUID 조회 (에러 발생 안 함)

    Args:
        db: 데이터베이스 세션
        user_identifier: 사용자 식별자 (email 또는 UUID string)

    Returns:
        User의 UUID 또는 None
    """
    user = get_user_by_identifier(db, user_identifier)
    return user.id if user else None