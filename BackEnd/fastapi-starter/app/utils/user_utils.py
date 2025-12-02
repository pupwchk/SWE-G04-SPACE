"""
사용자 관련 유틸리티 함수
Sendbird user_id(email)와 DB user_id(UUID) 매핑
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User


def get_user_by_identifier(db: Session, user_identifier: str) -> Optional[User]:
    """
    사용자 식별자(email 또는 UUID)로 User 조회

    Args:
        db: 데이터베이스 세션
        user_identifier: 사용자 식별자 (email 또는 UUID string)

    Returns:
        User 객체 또는 None
    """
    # 1. UUID로 시도
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
    return user


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