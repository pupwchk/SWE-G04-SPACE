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
    1. Email로 조회 (가장 확실한 방법)
    2. 서버 DB UUID로 조회
    3. Supabase UUID인 경우 → Supabase에서 이메일 조회 → Email로 조회

    Args:
        db: 데이터베이스 세션
        user_identifier: 사용자 식별자 (email 또는 UUID string)

    Returns:
        User 객체 또는 None
    """
    logger.debug(f"🔍 [USER-MAPPING] Looking up user_identifier: {user_identifier}")

    # 1. Email로 먼저 시도 (@ 포함 여부로 이메일 판단)
    if "@" in user_identifier:
        user = db.query(User).filter(User.email == user_identifier).first()
        if user:
            logger.debug(f"✅ [USER-MAPPING] Found by email: {user_identifier} → Server UUID {user.id}")
            return user
        else:
            logger.warning(f"⚠️ [USER-MAPPING] Email not found in server DB: {user_identifier}")
            return None

    # 2. UUID 형식인 경우
    try:
        user_uuid = UUID(user_identifier)

        # 2-1. 서버 DB UUID로 조회
        user = db.query(User).filter(User.id == user_uuid).first()
        if user:
            logger.debug(f"✅ [USER-MAPPING] Found by server UUID: {user_identifier}")
            return user

        # 2-2. 서버 DB에 없으면 Supabase UUID일 가능성 - Supabase에서 이메일 조회
        logger.info(f"🔄 [USER-MAPPING] UUID not found in server DB, checking Supabase: {user_identifier}")
        email = _get_email_from_supabase(user_identifier)

        if email:
            # 이메일로 서버 DB 재조회
            user = db.query(User).filter(User.email == email).first()
            if user:
                logger.info(f"✅ [USER-MAPPING] Mapped Supabase UUID {user_identifier} → Email {email} → Server UUID {user.id}")
                return user
            else:
                logger.warning(f"⚠️ [USER-MAPPING] Email {email} found in Supabase but not in server DB")
                return None
        else:
            logger.warning(f"⚠️ [USER-MAPPING] UUID {user_identifier} not found in Supabase either")
            return None

    except (ValueError, TypeError):
        # UUID 형식도 아니고 이메일도 아닌 경우
        logger.error(f"❌ [USER-MAPPING] Invalid user_identifier format: {user_identifier}")
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
            logger.warning(f"⚠️ [SUPABASE-MAPPING] Supabase service not available")
            return None

        client = supabase_persona_service.client

        # 방법 1: Supabase Auth Admin API로 사용자 조회
        try:
            logger.debug(f"🔍 [SUPABASE-MAPPING] Trying auth.admin.get_user_by_id for {user_id}")
            response = client.auth.admin.get_user_by_id(user_id)
            if response and response.user and response.user.email:
                email = response.user.email
                logger.info(f"✅ [SUPABASE-MAPPING] Found email via Auth API: {email} for UUID {user_id}")
                return email
        except AttributeError as e:
            logger.debug(f"ℹ️ [SUPABASE-MAPPING] Admin API not available: {str(e)}")
        except Exception as e:
            logger.debug(f"ℹ️ [SUPABASE-MAPPING] Auth API query failed: {str(e)}")

        # 방법 2: Supabase Database의 auth.users 테이블 직접 조회
        try:
            logger.debug(f"🔍 [SUPABASE-MAPPING] Trying direct database query for {user_id}")
            # auth.users는 직접 접근 불가능하므로 public.users 또는 profiles 테이블 시도
            result = client.table("users").select("email").eq("id", user_id).maybe_single().execute()
            if result.data and result.data.get("email"):
                email = result.data.get("email")
                logger.info(f"✅ [SUPABASE-MAPPING] Found email via DB query: {email} for UUID {user_id}")
                return email
        except Exception as e:
            logger.debug(f"ℹ️ [SUPABASE-MAPPING] DB query failed: {str(e)}")

        # 방법 3: profiles 테이블 시도 (일반적인 Supabase 패턴)
        try:
            logger.debug(f"🔍 [SUPABASE-MAPPING] Trying profiles table for {user_id}")
            result = client.table("profiles").select("email").eq("id", user_id).maybe_single().execute()
            if result.data and result.data.get("email"):
                email = result.data.get("email")
                logger.info(f"✅ [SUPABASE-MAPPING] Found email via profiles: {email} for UUID {user_id}")
                return email
        except Exception as e:
            logger.debug(f"ℹ️ [SUPABASE-MAPPING] Profiles query failed: {str(e)}")

        logger.warning(f"⚠️ [SUPABASE-MAPPING] No email found for Supabase UUID {user_id}")
        return None

    except Exception as e:
        logger.error(f"❌ [SUPABASE-MAPPING] Unexpected error querying Supabase: {str(e)}", exc_info=True)
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